"""Finite synthetic-pilot uncertainty for fixed projected development cells."""
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
from btp.evaluation import empirical_metrics, sample_mixture, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash
from representation_constrained import constrained_query_minimax, reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
OUTPUT = ROOT / "results/projected_pilot_sensitivity_v2_20261024"
PILOT_SIZES = (500, 1500, 5000, 15000)
REPEATS = 5
REF_PILOT_ROWS = 30000
FRESH_ROWS = 10000


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def pilot_matrix(models, workload, rows: int, seed: int) -> np.ndarray:
    return np.column_stack([
        workload.transform(model.sample(rows, seed + i)).mean(axis=0)
        for i, model in enumerate(models)
    ])


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()
        or cfg["profile"]["pilot_samples"] != 1500):
        raise ValueError("Source projected cell is incompatible")
    summary = np.load(cell / "releases/permitted_summary.npz")
    alpha, bcal, Hsource = (summary["alpha"], summary["target_query_mean"], summary["H"])
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    workload, audit = projected_workloads_v2(public_schema())
    declared = json.loads((cell / "workloads.json").read_text())
    expected = json.loads(json.dumps({"calibration": workload.to_dict(),
                                      "unseen_audit": audit.to_dict()}))
    if declared != expected:
        raise ValueError("Saved workload mismatch")
    regenerated = pilot_matrix(models, workload, 1500, cfg["seed"] + 900)
    if not np.array_equal(regenerated, Hsource):
        raise ValueError(f"Source H failed exact reproduction; max error {np.max(np.abs(regenerated-Hsource))}")
    prior_cfg = json.loads((CONSTRAINED / cell.name / "configuration.json").read_text())
    if prior_cfg["source_code_hash"] != cfg["code_hash"]:
        raise ValueError("Prior constrained weights use incompatible code")
    original = np.asarray(json.loads((CONSTRAINED / cell.name / "weight_fits.json").read_text())
                          ["constrained"]["weights"], float)
    source_fit, _ = constrained_query_minimax(Hsource, bcal, alpha, .25, .5)
    if not np.allclose(source_fit, original, atol=1e-7):
        raise ValueError("Source constrained weight vector failed reproduction")
    parts = reference_parts(cell, cfg, alpha)
    bval = weighted_reference(parts["validation"], workload, alpha)
    capacity(resources)
    Href = pilot_matrix(models, workload, REF_PILOT_ROWS, cfg["seed"] + 41000)
    empirical_oracle, oracle_cert = constrained_query_minimax(Href, bval, alpha, .25, .5)
    oracle_value = float(np.max(np.abs(Href @ empirical_oracle - bval)))
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "fixed_matrices.npz", H_source=Hsource, H_reference=Href,
                        b_calibration=bcal, b_validation=bval, alpha=alpha,
                        empirical_oracle_weights=empirical_oracle)
    rows, fit_records = [], []
    for size_index, n_pilot in enumerate(PILOT_SIZES):
        for rep in range(REPEATS):
            if time.monotonic() - started >= resources["cell_timeout_seconds"]:
                raise TimeoutError("Cell wall-time limit reached")
            capacity(resources)
            began = time.monotonic()
            pilot_seed = cfg["seed"] + 21000 + 100 * size_index + 10 * rep
            H = pilot_matrix(models, workload, n_pilot, pilot_seed)
            fitted, cert = constrained_query_minimax(H, bcal, alpha, .25, .5)
            fresh_seed = cfg["seed"] + 31000 + 100 * size_index + rep
            metrics = {}
            allocations = {}
            for method, vector in (("size", alpha), ("constrained", fitted)):
                synthetic, counts = sample_mixture(models, vector, FRESH_ROWS, fresh_seed)
                if counts.sum() != FRESH_ROWS or len(synthetic) != FRESH_ROWS:
                    raise RuntimeError("Fresh synthetic allocation mismatch")
                metrics[method] = empirical_metrics(parts["test"], synthetic, workload, audit, alpha)
                allocations[method] = counts.tolist()
            reference_value = float(np.max(np.abs(Href @ fitted - bval)))
            if reference_value + 1e-7 < oracle_value:
                raise RuntimeError("Fixed-reference LP certificate violated")
            rows.append({
                "pilot_per_client": n_pilot, "replicate": rep, "pilot_seed": pilot_seed,
                "fresh_seed": fresh_seed,
                "pilot_H_max_error_vs_independent_finite_H_ref": float(np.max(np.abs(H-Href))),
                "weight_l1_from_source_constrained": float(np.abs(fitted-original).sum()),
                "weight_l1_from_alpha": float(np.abs(fitted-alpha).sum()),
                "fixed_H_ref_validation_objective": reference_value,
                "fixed_H_ref_validation_oracle_objective": oracle_value,
                "fixed_H_ref_validation_excess": max(0., reference_value-oracle_value),
                "size_query_linf": metrics["size"]["query_linf"],
                "constrained_query_linf": metrics["constrained"]["query_linf"],
                "delta_query_linf": metrics["constrained"]["query_linf"]-metrics["size"]["query_linf"],
                "size_unseen_query_linf": metrics["size"]["unseen_query_linf"],
                "constrained_unseen_query_linf": metrics["constrained"]["unseen_query_linf"],
                "delta_unseen_query_linf": metrics["constrained"]["unseen_query_linf"]-metrics["size"]["unseen_query_linf"],
                "size_client_counts": json.dumps(allocations["size"]),
                "constrained_client_counts": json.dumps(allocations["constrained"]),
                "elapsed_seconds": time.monotonic()-began,
            })
            fit_records.append({"pilot_per_client": n_pilot, "replicate": rep,
                                "pilot_seed": pilot_seed, "weights": fitted.tolist(),
                                "solver_certificate": cert})
    frame = pd.DataFrame(rows)
    if len(frame) != len(PILOT_SIZES) * REPEATS:
        raise RuntimeError("Incomplete pilot-sensitivity table")
    frame.to_csv(out / "metrics.csv", index=False)
    (out / "fit_records.json").write_text(json.dumps(fit_records, indent=2) + "\n")
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "source_workloads_sha256": hashlib.sha256((cell / "workloads.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_H_reproduced_exactly": True,
        "pilot_sizes_per_client": list(PILOT_SIZES), "pilot_replicates": REPEATS,
        "independent_synthetic_reference_rows_per_client": REF_PILOT_ROWS,
        "fresh_synthetic_rows": FRESH_ROWS,
        "empirical_oracle_certificate": oracle_cert,
        "oracle_scope": "privileged fixed-finite-H reference and development validation only",
        "official_test_used": False, "reference_role": cfg["reference_role"],
        "elapsed_seconds": time.monotonic()-started,
        "ended_utc": datetime.now(timezone.utc).isoformat(), "status": "complete",
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
        started, completed = time.monotonic(), 0
        for generator, partition, k, seed in targets:
            if (completed >= args.max_cells or
                time.monotonic()-started >= resources["campaign_wall_seconds"]):
                break
            matches = list(SOURCE.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError("Expected one saved projected source cell")
            cell, = matches
            out = OUTPUT / cell.name
            marker = out / "configuration.json"
            if marker.exists():
                prior = json.loads(marker.read_text())
                if (prior.get("status") == "complete"
                    and prior.get("source_code_hash") == code_hash()
                    and prior.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible existing pilot output: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior failure retained: {out}")
            try:
                run_cell(cell, out, resources)
            except Exception as exc:
                out.mkdir(parents=True, exist_ok=True)
                (out / "failure.json").write_text(json.dumps({
                    "source_cell": str(cell.relative_to(ROOT)),
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "failed_utc": datetime.now(timezone.utc).isoformat(),
                }, indent=2) + "\n")
                raise
            completed += 1
        print("newly_completed", completed)


if __name__ == "__main__":
    main()
