"""Privileged empirical evaluator for saved maintained-MBI discrete draws."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.evaluation import empirical_metrics, weighted_reference
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP, public_schema
from btp.projected_workload import projected_workloads_v2
from scripts.representation_constrained import reference_parts

OUT = ROOT / "reports/published_references"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(package: dict, draw: Path, seed: int) -> tuple[pd.DataFrame, float]:
    arrays = np.load(draw)
    rng = np.random.default_rng(seed+77123)
    data = {}
    for c, domain in package["domain"].items():
        codes = arrays[c]
        if codes.min() < 0 or codes.max() >= len(domain["values"]):
            raise ValueError(f"Invalid PGM domain code: {c}")
        if domain["kind"] == "category":
            data[c] = np.asarray(domain["values"], dtype=object)[codes]
        else:
            intervals = np.asarray(domain["values"], int)
            lo, hi = intervals[codes].T
            data[c] = rng.integers(lo, hi+1)
    frame = pd.DataFrame(data)
    expected = frame.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
    known = expected.notna()
    raw_violation = float(frame.loc[known, "education-num"].ne(expected.loc[known]).mean())
    frame.loc[known, "education-num"] = expected.loc[known].astype(int)
    return frame, raw_violation


def main() -> None:
    manifest = json.loads((OUT / "pgm_cell_manifest.json").read_text())
    workload, audit = projected_workloads_v2(public_schema())
    rows, answers, statuses = [], [], []
    for entry in manifest["cells"]:
        cell = OUT / entry["name"]
        marker = cell / "pgm_complete.json"
        if not marker.is_file():
            statuses.append({"cell": entry["name"], "status": "failed_or_missing"})
            continue
        completed = json.loads(marker.read_text())
        if sha(cell / "model_mbi2.npz") != completed["model_checkpoint_sha256"]:
            raise ValueError("Maintained MBI checkpoint hash mismatch")
        package = json.loads((cell / "measurement_package.json").read_text())
        source = ROOT / package["source_cell"]
        cfg = json.loads((source / "configuration.json").read_text())
        alpha = np.asarray(json.loads((source / "partition.json").read_text())["alpha"], float)
        parts = reference_parts(source, cfg, alpha)
        real = weighted_reference(parts["test"], workload, alpha)
        pooled = workload.mean(pd.concat(parts["test"]))
        baseline = pd.read_csv(source / "exp01_test.csv")
        size = baseline.loc[baseline.method == "size"].sort_values("replicate")
        if len(size) != 5:
            raise ValueError("Missing matched size baseline")
        for item in completed["draws"]:
            draw = cell / item["path"]
            if sha(draw) != item["sha256"]:
                raise ValueError("Discrete PGM draw hash mismatch")
            synth, preprojection_violation = decode(package, draw, item["seed"])
            metrics = empirical_metrics(parts["test"], synth, workload, audit, alpha)
            q = workload.mean(synth)
            rep = item["replicate"]
            rows.append({"cell": entry["name"], "partition": cfg["partition"],
                         "k": cfg["k"], "seed": cfg["seed"], "replicate": rep,
                         "draw_seed": item["seed"], "reference_access": "aggregate_unnoised_query_means_only",
                         "formal_dp": False, "preprojection_education_relation_violation": preprojection_violation,
                         "size_baseline_query_linf_same_rep": float(size.iloc[rep].query_linf),
                         "pgm_minus_size": metrics["query_linf"] - float(size.iloc[rep].query_linf),
                         "pooled_reference_query_linf_secondary": float(np.abs(q-pooled).max()),
                         "measurement_payload_bytes": (cell / "measurement_package.json").stat().st_size,
                         "model_checkpoint_bytes": (cell / "model_mbi2.npz").stat().st_size,
                         **metrics})
            if rep == 0:
                synth.to_csv(cell / "decoded_projected_draw0.csv.gz", index=False,
                             compression={"method": "gzip", "mtime": 0})
            for query, real_value, pooled_value, syn_value in zip(workload.queries, real, pooled, q):
                answers.append({"cell": entry["name"], "replicate": rep, "query": query.name,
                                "real_alpha": float(real_value), "real_pooled_secondary": float(pooled_value),
                                "synthetic": float(syn_value), "absolute_error": float(abs(real_value-syn_value))})
        statuses.append({"cell": entry["name"], "status": "complete",
                         "fit_seconds": completed["fit_seconds"],
                         "calibration_query_linf": completed["query_linf_calibration"]})
    pd.DataFrame(statuses).to_csv(OUT / "pgm_status.csv", index=False)
    if rows:
        frame = pd.DataFrame(rows)
        frame.to_csv(OUT / "pgm_assessment_draws.csv", index=False)
        pd.DataFrame(answers).to_csv(OUT / "pgm_per_query.csv", index=False)
        cell = frame.groupby(["cell", "partition", "k", "seed"], as_index=False).agg(
            pgm_query_linf_mean=("query_linf", "mean"), size_query_linf_mean=("size_baseline_query_linf_same_rep", "mean"),
            pgm_minus_size_mean=("pgm_minus_size", "mean"),
            preprojection_relation_violation_mean=("preprojection_education_relation_violation", "mean"))
        cell.to_csv(OUT / "pgm_cell_means.csv", index=False)
    print(json.dumps({"complete_cells": len(rows)//5, "planned_cells": len(manifest["cells"])}))


if __name__ == "__main__":
    main()
