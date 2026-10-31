"""Summarize matched raw-versus-mapped education-number development samples."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/core_matrix_audit_20261024/manifest.csv"
SOURCE = ROOT / "results/education_projection_ablation_fixed_20261024"
OUT = ROOT / "reports/education_projection_20261024"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    rows = []
    for item in manifest.itertuples():
        cell = ROOT / item.cell
        output = SOURCE / cell.name
        config = json.loads((output / "configuration.json").read_text())
        if (
            config["status"] != "complete" or config["official_test_used"]
            or config["source_cell"] != item.cell or config["repeats"] != 5
        ):
            raise ValueError(f"Incompatible projection cell: {output}")
        metrics = pd.read_csv(output / "metrics.csv")
        if len(metrics) != 20 or not (
            metrics.groupby(["method", "projection"]).size() == 5
        ).all():
            raise ValueError(f"Missing matched samples: {output}")
        for (method, projection), group in metrics.groupby(
            ["method", "projection"]
        ):
            rows.append({
                "cell": item.cell,
                "generator": item.generator,
                "partition": item.partition,
                "k": item.k,
                "split_seed": item.seed,
                "method": method,
                "projection": projection,
                "query_linf_mean": float(group.query_linf.mean()),
                "audit_query_linf_mean": float(
                    group.unseen_query_linf.mean()
                ),
                "education_relation_mismatch_mean": float(
                    group.education_relation_mismatch.mean()
                ),
                "unmapped_education_rate_mean": float(
                    group.unmapped_education_rate.mean()
                ),
            })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "cell_method_projection_means.csv", index=False)
    wide = frame.pivot(
        index=["cell", "generator", "partition", "k", "split_seed"],
        columns=["method", "projection"],
        values=[
            "query_linf_mean", "audit_query_linf_mean",
            "education_relation_mismatch_mean",
            "unmapped_education_rate_mean",
        ],
    )
    expected = {
        ("size", "raw_model_sample"),
        ("size", "mapped_education_number"),
        ("constrained", "raw_model_sample"),
        ("constrained", "mapped_education_number"),
    }
    if {
        (method, projection) for _, method, projection in wide.columns
    } != expected:
        raise ValueError("Method/projection coverage mismatch")
    q = wide["query_linf_mean"]
    a = wide["audit_query_linf_mean"]
    e = wide["education_relation_mismatch_mean"]
    u = wide["unmapped_education_rate_mean"]
    paired = pd.DataFrame({
        "size_raw_query": q[("size", "raw_model_sample")],
        "size_projected_query": q[("size", "mapped_education_number")],
        "constrained_raw_query": q[("constrained", "raw_model_sample")],
        "constrained_projected_query": q[("constrained", "mapped_education_number")],
        "size_raw_audit": a[("size", "raw_model_sample")],
        "size_projected_audit": a[("size", "mapped_education_number")],
        "size_raw_relation_mismatch": e[("size", "raw_model_sample")],
        "size_projected_relation_mismatch": e[("size", "mapped_education_number")],
        "constrained_raw_relation_mismatch": e[("constrained", "raw_model_sample")],
        "constrained_projected_relation_mismatch": e[("constrained", "mapped_education_number")],
        "unmapped_education_rate": u[("size", "raw_model_sample")],
    }).reset_index()
    paired["repair_size_primary_delta"] = (
        paired.size_projected_query - paired.size_raw_query
    )
    paired["repair_size_audit_delta"] = (
        paired.size_projected_audit - paired.size_raw_audit
    )
    paired["weighting_before_repair_delta"] = (
        paired.constrained_raw_query - paired.size_raw_query
    )
    paired["weighting_after_repair_delta"] = (
        paired.constrained_projected_query - paired.size_projected_query
    )
    paired.to_csv(OUT / "paired_cell_effects.csv", index=False)
    summary = (
        paired.groupby(["generator", "partition", "k"])
        .agg(
            split_seeds=("split_seed", "nunique"),
            size_raw_relation_mismatch=(
                "size_raw_relation_mismatch", "mean"
            ),
            size_projected_relation_mismatch=(
                "size_projected_relation_mismatch", "mean"
            ),
            unmapped_education_rate=("unmapped_education_rate", "mean"),
            repair_size_primary_delta=("repair_size_primary_delta", "mean"),
            repair_size_audit_delta=("repair_size_audit_delta", "mean"),
            weighting_before_repair_delta=(
                "weighting_before_repair_delta", "mean"
            ),
            weighting_after_repair_delta=(
                "weighting_after_repair_delta", "mean"
            ),
        )
        .reset_index()
    )
    summary.to_csv(OUT / "slice_effects.csv", index=False)
    overview = {
        "complete_cells": len(paired),
        "raw_size_relation_mismatch_by_generator": (
            paired.groupby("generator").size_raw_relation_mismatch.mean().to_dict()
        ),
        "projected_size_relation_mismatch_by_generator": (
            paired.groupby("generator").size_projected_relation_mismatch.mean().to_dict()
        ),
        "repair_size_primary_delta_by_generator": (
            paired.groupby("generator").repair_size_primary_delta.mean().to_dict()
        ),
        "repair_changes_primary_max_cells": int(
            (paired.repair_size_primary_delta.abs() > 1e-12).sum()
        ),
        "initial_unknown_category_failure_retained": (
            ROOT / "results/education_projection_ablation_20261024"
        ).exists(),
        "scope": "postpilot TRAIN-verified projection; scores refer to raw model; no global selection or official test",
    }
    (OUT / "overview.json").write_text(json.dumps(overview, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(7, 5))
    for generator, group in paired.groupby("generator"):
        ax.scatter(
            group.size_raw_relation_mismatch,
            group.size_projected_relation_mismatch,
            label=generator, alpha=0.75,
        )
    ax.set_xlabel("Raw size-sample education mismatch")
    ax.set_ylabel("Projected size-sample education mismatch")
    ax.set_title("Adult development: TRAIN-verified education-code projection")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "education_relation_repair.png", dpi=160)
    print(json.dumps(overview, indent=2))


if __name__ == "__main__":
    main()
