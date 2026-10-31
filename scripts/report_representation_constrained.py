"""Report the preregistered fixed-target representation comparison."""

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
SOURCE = ROOT / "results/representation_constrained_20261024"
OUT = ROOT / "reports/representation_constrained_20261024"
PRACTICAL_GAIN = -0.005
AUDIT_DETERIORATION_LIMIT = 0.005


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    rows = []
    for item in manifest.itertuples():
        cell = ROOT / item.cell
        output = SOURCE / cell.name
        config_path = output / "configuration.json"
        if not config_path.exists():
            raise ValueError(f"Missing completed representation cell: {output}")
        config = json.loads(config_path.read_text())
        if (
            config["status"] != "complete" or config["official_test_used"]
            or config["source_cell"] != item.cell
            or config["assessment_repeats"] != 5
        ):
            raise ValueError(f"Incompatible result: {output}")
        fits = json.loads((output / "weight_fits.json").read_text())
        constrained = fits["constrained"]
        if (
            not constrained["success"]
            or constrained["actual_weight_l1"] > 0.25 + 1e-7
            or constrained["minimum_weight_alpha_ratio"] < 0.5 - 1e-7
        ):
            raise ValueError(f"Representation constraint violation: {output}")
        metrics = pd.read_csv(output / "metrics.csv")
        assessment = metrics[metrics.split == "development_assessment"]
        if (
            set(assessment.method) != {"size", "constrained", "unconstrained"}
            or not (assessment.groupby("method").size() == 5).all()
            or assessment.query_linf.isna().any()
        ):
            raise ValueError(f"Assessment repetition/metric error: {output}")
        size = assessment[assessment.method == "size"]
        for method, group in assessment.groupby("method"):
            rows.append({
                "source_cell": item.cell,
                "generator": item.generator,
                "partition": item.partition,
                "k": item.k,
                "split_seed": item.seed,
                "source_status": item.status,
                "method": method,
                "assessment_query_linf_mean": float(group.query_linf.mean()),
                "assessment_query_linf_synthetic_sd": float(
                    group.query_linf.std()
                ),
                "assessment_unseen_query_linf_mean": float(
                    group.unseen_query_linf.mean()
                ),
                "paired_delta_vs_size": float(
                    group.query_linf.mean() - size.query_linf.mean()
                ),
                "audit_delta_vs_size": float(
                    group.unseen_query_linf.mean()
                    - size.unseen_query_linf.mean()
                ),
                "weight_l1_from_alpha": float(group.weight_l1_from_alpha.iloc[0]),
                "minimum_weight_alpha_ratio": float(
                    group.minimum_weight_alpha_ratio.iloc[0]
                ),
                "effective_client_count": float(
                    group.effective_client_count.iloc[0]
                ),
                "alpha_vs_pooled_reference_query_linf": float(
                    config["assessment_target_gap_query_linf"]
                ),
                "pooled_reference_query_linf_secondary": float(
                    group.pooled_reference_query_linf_secondary.mean()
                ),
                "synthetic_repeats": len(group),
            })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "cell_method_means.csv", index=False)
    summary = (
        frame.groupby(["generator", "partition", "k", "method"])
        .agg(
            split_seeds=("split_seed", "nunique"),
            mean_primary_delta=("paired_delta_vs_size", "mean"),
            min_primary_delta=("paired_delta_vs_size", "min"),
            max_primary_delta=("paired_delta_vs_size", "max"),
            mean_audit_delta=("audit_delta_vs_size", "mean"),
            mean_weight_l1=("weight_l1_from_alpha", "mean"),
            min_weight_alpha_ratio=("minimum_weight_alpha_ratio", "min"),
            mean_effective_clients=("effective_client_count", "mean"),
            mean_target_estimand_gap=(
                "alpha_vs_pooled_reference_query_linf", "mean"
            ),
        )
        .reset_index()
    )
    summary["practical_primary_gain"] = (
        summary.mean_primary_delta <= PRACTICAL_GAIN
    )
    summary["audit_guardrail"] = (
        summary.mean_audit_delta <= AUDIT_DETERIORATION_LIMIT
    )
    summary["fidelity_and_audit_screen"] = (
        summary.practical_primary_gain & summary.audit_guardrail
    )
    summary.to_csv(OUT / "slice_method_summary.csv", index=False)
    constrained = summary[summary.method == "constrained"]
    unconstrained = summary[summary.method == "unconstrained"]
    overview = {
        "complete_cells": int(frame.source_cell.nunique()),
        "assessment_draws_per_method_per_cell": 5,
        "constrained_practical_gain_slices": int(
            constrained.practical_primary_gain.sum()
        ),
        "constrained_fidelity_and_audit_screen_slices": int(
            constrained.fidelity_and_audit_screen.sum()
        ),
        "unconstrained_practical_gain_slices": int(
            unconstrained.practical_primary_gain.sum()
        ),
        "total_slices_per_method": len(constrained),
        "practical_gain_margin": PRACTICAL_GAIN,
        "audit_deterioration_limit": AUDIT_DETERIORATION_LIMIT,
        "scope": "development fidelity/audit screen only; utility, subgroup, privacy, resources and global freeze unresolved",
        "official_test_used": False,
    }
    (OUT / "overview.json").write_text(json.dumps(overview, indent=2) + "\n")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, generator in zip(
        axes, ["copula", "chow_liu", "mixed_gmm"]
    ):
        subset = summary[
            (summary.generator == generator)
            & summary.method.isin(["constrained", "unconstrained"])
        ]
        for method, group in subset.groupby("method"):
            ax.scatter(
                group.mean_weight_l1, group.mean_primary_delta,
                label=method, alpha=0.8,
            )
        ax.axhline(0, color="gray", lw=0.8)
        ax.axhline(PRACTICAL_GAIN, color="green", ls="--", lw=0.8)
        ax.axvline(0.25, color="black", ls=":", lw=0.8)
        ax.set_title(generator)
        ax.set_xlabel("Mean L1 shift from alpha")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Mean paired query-max difference vs size")
    axes[-1].legend(fontsize=8)
    fig.suptitle(
        "Adult development slices; three overlapping split seeds, five synthetic draws per cell"
    )
    fig.tight_layout()
    fig.savefig(OUT / "fidelity_representation_frontier.png", dpi=160)
    print(json.dumps(overview, indent=2))


if __name__ == "__main__":
    main()
