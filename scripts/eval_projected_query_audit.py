"""Per-query D_R/D_S answers and conditional simultaneous sampling radius."""
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
from btp.evaluation import sample_mixture, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash
from representation_constrained import reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
OUTPUT = ROOT / "results/projected_query_audit_20261025"
ROWS, REPEATS, DELTA = 10000, 5, .05


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def support_stratum(mass: float) -> str:
    return "rare_lt_1pct" if mass < .01 else ("low_1_to_5pct" if mass < .05 else "common_ge_5pct")


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Incompatible projected development cell")
    audit_cell = CONSTRAINED / cell.name
    prior_cfg = json.loads((audit_cell / "configuration.json").read_text())
    if (prior_cfg["source_code_hash"] != cfg["code_hash"]
        or prior_cfg["rows"] != ROWS or prior_cfg["assessment_repeats"] != REPEATS):
        raise ValueError("Prior constrained audit incompatible")
    prior = pd.read_csv(audit_cell / "metrics.csv")
    prior = prior.loc[(prior.split == "development_assessment") &
                      prior.method.isin(["size", "constrained"])]
    if len(prior) != 2*REPEATS:
        raise ValueError("Prior five-draw reference incomplete")
    fitted = json.loads((audit_cell / "weight_fits.json").read_text())
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    vectors = {method: np.asarray(fitted[method]["weights"], float)
               for method in ("size", "constrained")}
    if not np.allclose(vectors["size"], alpha):
        raise ValueError("Size vector differs from alpha")
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    workloads = projected_workloads_v2(public_schema())
    declared = json.loads((cell / "workloads.json").read_text())
    expected = json.loads(json.dumps({"calibration": workloads[0].to_dict(),
                                      "unseen_audit": workloads[1].to_dict()}))
    if declared != expected:
        raise ValueError("Workload version mismatch")
    parts = reference_parts(cell, cfg, alpha)["test"]
    pooled = pd.concat(parts)
    L = sum(len(workload.queries) for workload in workloads)
    n_effective_term = sum(float(a*a/len(part)) for a, part in zip(alpha, parts))
    radius = float(np.sqrt(.5*np.log(2*L/DELTA)*(n_effective_term+1/ROWS)))
    real = {}
    for name, workload in zip(("primary", "unseen_audit"), workloads):
        real[name] = {
            "alpha": weighted_reference(parts, workload, alpha),
            "pooled": workload.mean(pooled),
            "count": workload.transform(pooled).sum(axis=0).astype(int),
        }
    answer_rows, draw_rows = [], []
    for method, vector in vectors.items():
        for rep in range(REPEATS):
            if time.monotonic()-started >= resources["cell_timeout_seconds"]:
                raise TimeoutError("Query-audit cell wall time reached")
            capacity(resources)
            seed = cfg["seed"]+5200+rep
            synthetic, counts = sample_mixture(models, vector, ROWS, seed)
            if len(synthetic) != ROWS or counts.sum() != ROWS:
                raise RuntimeError("Mixture allocation mismatch")
            primary_error = None
            for name, workload in zip(("primary", "unseen_audit"), workloads):
                answers = workload.mean(synthetic)
                reference = real[name]
                absolute = np.abs(answers-reference["alpha"])
                if name == "primary":
                    primary_error = float(absolute.max())
                for q, estimate, truth, pooled_truth, count, error in zip(
                    workload.queries, answers, reference["alpha"],
                    reference["pooled"], reference["count"], absolute):
                    arity = 2 if q.name == "education_number_relation_violation_v2" else len(q.terms)
                    answer_rows.append({"method": method, "replicate": rep, "seed": seed,
                        "workload": name, "query": q.name, "arity": arity,
                        "real_alpha_answer": float(truth),
                        "real_unweighted_pooled_answer_secondary": float(pooled_truth),
                        "real_pooled_matching_count": int(count),
                        "real_pooled_n": len(pooled),
                        "support_stratum": support_stratum(float(truth)),
                        "synthetic_answer": float(estimate),
                        "signed_error": float(estimate-truth),
                        "absolute_error": float(error),
                        "conditional_simultaneous_95_radius": radius})
            baseline = prior.loc[(prior.method == method) & (prior.replicate == rep)]
            if len(baseline) != 1 or not np.isclose(primary_error, baseline.query_linf.iloc[0], atol=1e-10):
                raise ValueError(f"Primary metric failed saved-draw reproduction: {cell.name}/{method}/{rep}")
            draw_rows.append({"method": method, "replicate": rep, "seed": seed,
                "client_counts": json.dumps(counts.tolist()),
                "query_linf": primary_error,
                "saved_query_linf": float(baseline.query_linf.iloc[0]),
                "conditional_simultaneous_95_radius": radius})
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(answer_rows).to_csv(out / "query_answers.csv", index=False)
    pd.DataFrame(draw_rows).to_csv(out / "draw_metrics.csv", index=False)
    (out / "uncertainty.json").write_text(json.dumps({
        "confidence_nominal": 1-DELTA,
        "L_queries_primary_and_audit": L,
        "alpha_weighted_real_n_term": n_effective_term,
        "synthetic_n_term": 1/ROWS,
        "simultaneous_hoeffding_union_radius": radius,
        "assumptions": "independent bounded real records within clients and independent synthetic rows; not verified for Adult",
        "interpretation": "conditional radius around expected two-sample query differences, not measured population distance or validated Adult confidence interval",
    }, indent=2) + "\n")
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "source_workloads_sha256": hashlib.sha256((cell / "workloads.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "methods": list(vectors), "synthetic_rows": ROWS, "replicates": REPEATS,
        "primary_reference": "alpha-standardized development-assessment client rows",
        "pooled_reference": "secondary unweighted development-assessment rows",
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
        began, completed = time.monotonic(), 0
        for generator, partition, k, seed in targets:
            if completed >= args.max_cells or time.monotonic()-began >= resources["campaign_wall_seconds"]:
                break
            matches = list(SOURCE.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError("Expected one source cell")
            cell, = matches
            out = OUTPUT / cell.name
            marker = out / "configuration.json"
            if marker.exists():
                prior = json.loads(marker.read_text())
                if (prior.get("status") == "complete" and prior.get("source_code_hash") == code_hash()
                    and prior.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible existing query audit: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior query-audit failure retained: {out}")
            try:
                capacity(resources)
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
