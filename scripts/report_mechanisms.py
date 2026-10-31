"""Rebuild fixed Exp9/10 contrast tables from saved artifacts without refitting."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/mechanisms"
SEVERITY = ROOT / "results/severity_fixed_quantity_20261025"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(kind: str) -> tuple[pd.DataFrame, list]:
    source = OUT / ("projection" if kind == "projection" else "summary_ablation")
    cells, failures = [], []
    for spec in json.loads((OUT / f"{kind}_cell_manifest.json").read_text())["cells"]:
        path = source / Path(spec["source_cell"]).name
        marker = path / "complete.json"
        if not marker.is_file():
            failures.append({**spec, "status": "failed_or_missing"})
            continue
        if sha(path / "metrics.csv") != json.loads(marker.read_text())["metrics_sha256"]:
            raise ValueError(f"Mechanism artifact hash mismatch: {path}")
        cells.append(pd.read_csv(path / "metrics.csv"))
    return (pd.concat(cells, ignore_index=True) if cells else pd.DataFrame()), failures


def report_projection() -> dict:
    frame, failures = collect("projection")
    if not frame.empty:
        frame.to_csv(OUT / "projection_all_draws.csv", index=False)
        pivot = frame.pivot(index=["cell", "generator", "partition", "k", "seed", "method", "replicate"],
                            columns="sample_type", values="query_linf").reset_index()
        pivot["projected_minus_raw"] = pivot["projected_same_rows"] - pivot["raw"]
        pivot.to_csv(OUT / "projection_paired_draws.csv", index=False)
        summary = pivot.groupby(["generator", "partition", "method"], as_index=False).agg(
            draws=("replicate", "count"), mean_projected_minus_raw=("projected_minus_raw", "mean"),
            mean_raw_loss=("raw", "mean"), mean_projected_loss=("projected_same_rows", "mean"))
        summary.to_csv(OUT / "projection_summary.csv", index=False)
        relation = frame.groupby(["generator", "partition", "method", "sample_type"], as_index=False).agg(
            mean_mapped_relation_violation=("mapped_relation_violation", "mean"))
        relation.to_csv(OUT / "projection_relation.csv", index=False)
    return {"completed_cells": 0 if frame.empty else frame.cell.nunique(), "failed_cells": len(failures)}


def report_summaries() -> dict:
    frame, failures = collect("summaries")
    if not frame.empty:
        frame.to_csv(OUT / "summary_ablation_all_draws.csv", index=False)
        cell = frame.groupby(["cell", "partition", "k", "seed", "variant"], as_index=False).agg(
            query_linf_mean=("query_linf", "mean"), audit_linf_mean=("unseen_query_linf", "mean"),
            weight_l1=("weight_l1", "first"))
        cell.to_csv(OUT / "summary_ablation_cell_means.csv", index=False)
        pivot = cell.pivot(index=["cell", "partition", "k", "seed"], columns="variant",
                           values="query_linf_mean").reset_index()
        for variant in ("one_way", "one_two_way", "full"):
            pivot[f"{variant}_minus_size"] = pivot[variant] - pivot["size"]
        pivot.to_csv(OUT / "summary_ablation_paired.csv", index=False)
        release = []
        for spec in json.loads((OUT / "summaries_cell_manifest.json").read_text())["cells"]:
            path = OUT / "summary_ablation" / Path(spec["source_cell"]).name / "weight_fits.json"
            if path.is_file():
                data = json.loads(path.read_text())
                for name, cert in data["certificates"].items():
                    release.append({"cell": Path(spec["source_cell"]).name, "variant": name,
                                    "query_count": cert["query_count"],
                                    "released_payload_bytes_npz": cert["released_payload_bytes_npz"]})
        pd.DataFrame(release).to_csv(OUT / "summary_release_bytes.csv", index=False)
    return {"completed_cells": 0 if frame.empty else frame.cell.nunique(), "failed_cells": len(failures)}


def report_severity() -> dict:
    records, achievements, failures = [], [], []
    for spec in json.loads((OUT / "severity_cell_manifest.json").read_text())["cells"]:
        severity = spec["severity"]
        cell = SEVERITY / f'copula_age_k5_s{spec["seed"]}_severity{str(severity).replace(".", "p")}'
        marker = cell / "complete.json"
        if not marker.is_file():
            failures.append({**spec, "status": "unsupported" if (cell / "unsupported.json").is_file() else "failed_or_missing"})
            continue
        if sha(cell / "metrics.csv") != json.loads(marker.read_text())["metrics_sha256"]:
            raise ValueError(f"Severity artifact hash mismatch: {cell}")
        records.append(pd.read_csv(cell / "metrics.csv"))
        assignment = json.loads((cell / "achieved_assignment.json").read_text())
        ages = assignment["train_age_means"]
        edu = assignment["train_education_num_means"]
        weights = json.loads((cell / "weight_fits.json").read_text())
        achievements.append({"seed": spec["seed"], "severity": severity,
                             "age_mean_range": max(ages)-min(ages),
                             "education_num_mean_range": max(edu)-min(edu),
                             "mean_local_tune_query_mae": float(np.mean(weights["local_tune_mae"])),
                             "oracle_pilot_objective": weights["fixed_pilot_validation_oracle"]["objective_calibration_query_linf"]})
    if records:
        frame = pd.concat(records, ignore_index=True)
        frame.to_csv(OUT / "severity_all_draws.csv", index=False)
        cell = frame.groupby(["seed", "severity", "method"], as_index=False).agg(
            query_linf_mean=("query_linf", "mean"), audit_linf_mean=("unseen_query_linf", "mean"),
            weight_l1=("weight_l1", "first"))
        cell.to_csv(OUT / "severity_cell_means.csv", index=False)
        pd.DataFrame(achievements).to_csv(OUT / "severity_achieved.csv", index=False)
        if len(achievements) == 6:
            pivot = cell.pivot(index=["seed", "method"], columns="severity", values="query_linf_mean").reset_index()
            pivot["high_minus_low"] = pivot[.85] - pivot[.25]
            pivot.to_csv(OUT / "severity_paired_contrasts.csv", index=False)
    return {"completed_cells": len(records), "failed_or_unsupported": len(failures)}


def main() -> None:
    result = {"projection": report_projection(), "summary_ablation": report_summaries(),
              "severity": report_severity()}
    (OUT / "mechanism_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
