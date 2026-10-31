"""Matched development sample-size audit over fixed projected local models."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from btp.evaluation import empirical_metrics, sample_mixture
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash
from representation_constrained import reference_parts

SMALL, BASE, LARGE = 2500, 10000, 40000
REPEATS = 5
SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
OUTPUT = ROOT / "results/projected_sample_size_20261024"


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared memory reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Source cell is incompatible or official-test scoped")
    audit_cell = CONSTRAINED / cell.name
    prior_cfg = json.loads((audit_cell / "configuration.json").read_text())
    if (prior_cfg["source_code_hash"] != cfg["code_hash"] or prior_cfg["rows"] != BASE
        or prior_cfg["assessment_repeats"] != REPEATS
        or prior_cfg["source_manifest_sha256"]
        != hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest()):
        raise ValueError("Saved 10,000-row constrained audit is incompatible")
    weights = json.loads((audit_cell / "weight_fits.json").read_text())
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    vectors = {method: np.asarray(weights[method]["weights"], float)
               for method in ("size", "constrained")}
    if not np.allclose(vectors["size"], alpha):
        raise ValueError("Size weights differ from alpha")
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    workload, audit = projected_workloads_v2(public_schema())
    declared = json.loads((cell / "workloads.json").read_text())
    expected = {"calibration": workload.to_dict(), "unseen_audit": audit.to_dict()}
    if declared != json.loads(json.dumps(expected)):
        raise ValueError("Saved query workload differs")
    parts = reference_parts(cell, cfg, alpha)["test"]
    prior = pd.read_csv(audit_cell / "metrics.csv")
    prior = prior[(prior.split == "development_assessment") &
                  (prior.method.isin(["size", "constrained"]))].copy()
    if (len(prior) != 2 * REPEATS or not (prior.n_synthetic == BASE).all()
        or set(prior.replicate) != set(range(REPEATS))
        or any(int(row.seed) != cfg["seed"] + 5200 + int(row.replicate)
               for row in prior.itertuples(index=False))):
        raise ValueError("Saved 10,000-row replicates incomplete")
    rows = []
    for source_row in prior.itertuples(index=False):
        rows.append({"method": source_row.method, "m": BASE,
                     "replicate": int(source_row.replicate), "seed": int(source_row.seed),
                     "query_linf": float(source_row.query_linf),
                     "query_mae": float(source_row.query_mae),
                     "unseen_query_linf": float(source_row.unseen_query_linf),
                     "unseen_query_mae": float(source_row.unseen_query_mae),
                     "invalid_income_rate": float(source_row.invalid_income_rate),
                     "unique_row_fraction": float(source_row.unique_row_fraction),
                     "allocation": "see source constrained metrics; exact 10,000 rows",
                     "elapsed_seconds": None, "reused_compatible_prior": True})
    for m in (SMALL, LARGE):
        for rep in range(REPEATS):
            if time.monotonic() - started >= resources["cell_timeout_seconds"]:
                raise TimeoutError("Cell wall-time limit reached")
            seed = cfg["seed"] + 5200 + rep
            for method, vector in vectors.items():
                capacity(resources)
                began_draw = time.monotonic()
                synthetic, counts = sample_mixture(models, vector, m, seed)
                if counts.sum() != m or len(synthetic) != m:
                    raise RuntimeError("Mixture row allocation mismatch")
                metrics = empirical_metrics(parts, synthetic, workload, audit, alpha)
                rows.append({"method": method, "m": m, "replicate": rep, "seed": seed,
                             **{key: metrics[key] for key in ("query_linf", "query_mae",
                                "unseen_query_linf", "unseen_query_mae", "invalid_income_rate",
                                "unique_row_fraction")},
                             "allocation": json.dumps(counts.tolist()),
                             "elapsed_seconds": time.monotonic() - began_draw,
                             "reused_compatible_prior": False})
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    if len(frame) != 2 * 3 * REPEATS or frame.groupby(["method", "m"]).size().min() != REPEATS:
        raise RuntimeError("Incomplete sample-size table")
    frame.to_csv(out / "metrics.csv", index=False)
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": prior_cfg["source_manifest_sha256"],
        "source_workloads_sha256": prior_cfg["source_workloads_sha256"],
        "prior_constrained_script_sha256": prior_cfg["script_sha256"],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "methods": list(vectors), "m_values": [SMALL, BASE, LARGE],
        "replicates": REPEATS, "reference_role": cfg["reference_role"],
        "official_test_used": False, "status": "complete",
        "elapsed_seconds": time.monotonic() - started,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(cell.name, "complete", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cells", type=int, default=6)
    args = parser.parse_args()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease_path = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    targets = [(generator, partition, k, seed)
        for generator, partition, k in (("chow_liu", "age", 5),
                                        ("mixed_gmm", "label_skew", 10))
        for seed in (101, 202, 303)]
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        started = time.monotonic()
        newly_completed = 0
        for generator, partition, k, seed in targets:
            if (time.monotonic() - started >= resources["campaign_wall_seconds"]
                or newly_completed >= args.max_cells):
                break
            matches = list(SOURCE.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError(f"Expected one source cell for {generator}/{partition}/K{k}/seed{seed}")
            cell = matches[0]
            out = OUTPUT / cell.name
            if (out / "configuration.json").exists():
                previous = json.loads((out / "configuration.json").read_text())
                if (previous.get("status") == "complete"
                    and previous.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                    and previous.get("source_code_hash") == code_hash()):
                    continue
                raise RuntimeError(f"Incompatible existing output: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior cell failure retained: {out}")
            try:
                run_cell(cell, out, resources)
                newly_completed += 1
            except Exception as exc:
                out.mkdir(parents=True, exist_ok=True)
                (out / "failure.json").write_text(json.dumps({
                    "source_cell": str(cell.relative_to(ROOT)),
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "failed_utc": datetime.now(timezone.utc).isoformat(),
                }, indent=2) + "\n")
                raise
        print("newly_completed", newly_completed)


if __name__ == "__main__":
    main()
