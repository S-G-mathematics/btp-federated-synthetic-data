"""Summarize paired exact/approximate joint-implied development prediction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def markdown(frame: pd.DataFrame) -> str:
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{x:.6f}" if isinstance(x, float) else str(x) for x in row) + " |")
    return "\n".join(lines)


def report(root: Path, out: Path) -> None:
    paths = sorted(root.glob("*/configuration.json"))
    if len(paths) != 6:
        raise ValueError(f"Expected six completed joint-prediction cells, found {len(paths)}")
    metrics, coverage = [], []
    for path in paths:
        cfg = json.loads(path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Invalid joint cell: {path}")
        name = path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        expected_kind = "exact_discretized" if family == "chow_liu_age_k5" else "approximate"
        if cfg["score_kind"] != expected_kind:
            raise ValueError(f"Unexpected score interpretation: {path}")
        seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(path.parent / "covered_prediction_metrics.csv")
        cover = pd.read_csv(path.parent / "coverage.csv")
        paired = pd.read_csv(path.parent / "paired_predictions_evaluator_private.csv.gz",
                             dtype={"row_id": str})
        if (set(cover.joint_method) != {"size", "constrained"}
            or set(frame.predictor) != {"joint_implied", "synthetic_logistic",
                "synthetic_extra_trees", "TRTR_privileged_logistic",
                "TRTR_privileged_extra_trees"}
            or len(paired) != 2 * int(cover.query("joint_method == 'size' and client == 'alpha_global'").n.iloc[0])
            or paired.groupby("joint_method").row_id.nunique().min() * 2 != len(paired)):
            raise ValueError(f"Incomplete paired joint predictions: {path.parent}")
        for method, part in paired.groupby("joint_method"):
            covered = part.coverage_reason.eq("covered")
            if (part.loc[covered, "p_joint"].isna().any()
                or (~part.loc[covered, "p_joint"].between(0, 1)).any()
                or part.loc[~covered, "p_joint"].notna().any()):
                raise ValueError(f"Invalid posterior/abstention: {path.parent}/{method}")
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", seed)
        cover.insert(0, "family", family)
        cover.insert(1, "split_seed", seed)
        metrics.append(frame)
        coverage.append(cover)
    metrics = pd.concat(metrics, ignore_index=True)
    coverage = pd.concat(coverage, ignore_index=True)
    global_rows = metrics.query("client == 'alpha_global'")
    summary = global_rows.groupby(["family", "joint_method", "predictor"], as_index=False).agg(
        auroc_mean=("auroc", "mean"), auroc_min_seed=("auroc", "min"),
        auroc_max_seed=("auroc", "max"),
        auprc_mean=("auprc", "mean"), brier_mean=("brier", "mean"),
        log_loss_mean=("log_loss", "mean"), ece_fixed10_mean=("ece_fixed10", "mean"))
    pivot = global_rows.pivot(index=["family", "split_seed", "joint_method"],
                              columns="predictor", values=["auroc", "brier", "log_loss"]).reset_index()
    pivot.columns = ["_".join(str(part) for part in col if part) if isinstance(col, tuple) else col
                     for col in pivot.columns]
    paired_diffs = pivot[["family", "split_seed", "joint_method"]].copy()
    for metric in ("auroc", "brier", "log_loss"):
        for comparator in ("synthetic_logistic", "synthetic_extra_trees",
                           "TRTR_privileged_logistic", "TRTR_privileged_extra_trees"):
            paired_diffs[f"joint_minus_{comparator}_{metric}"] = (
                pivot[f"{metric}_joint_implied"]-pivot[f"{metric}_{comparator}"])
    coverage_global = coverage.query("client == 'alpha_global'").groupby(
        ["family", "joint_method"], as_index=False).agg(
        n_min=("n", "min"), alpha_coverage_mean=("alpha_weighted_coverage", "mean"),
        alpha_coverage_min_seed=("alpha_weighted_coverage", "min"),
        off_support_rows_total=("both_labels_zero_mass", "sum"),
        nonfinite_rows_total=("nonfinite_denominator", "sum"))
    out.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out / "all_prediction_metrics.csv", index=False)
    coverage.to_csv(out / "all_coverage.csv", index=False)
    summary.to_csv(out / "global_summary.csv", index=False)
    paired_diffs.to_csv(out / "paired_differences.csv", index=False)
    coverage_global.to_csv(out / "coverage_summary.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Projected joint-implied income development audit", "",
        "Chow-Liu is exact for its fitted projected discrete model. Mixed GMM uses a normalized approximate score. All comparisons are on the same covered development-assessment people, with alpha-standardized global weights. Official Adult test was not evaluated.", "",
        "## Coverage", "", markdown(coverage_global), "",
        "## Predictive scores", "", markdown(summary), "",
        "The paired-differences CSV contains joint minus trained-predictor AUROC/Brier/log-loss by split seed. TRTR is a privileged pooled-real diagnostic. Coverage says only whether the fitted route assigns support; it does not establish conditional correctness. Overlapping Adult splits are not independent cohorts.", "",
    ]))
    print(coverage_global.to_string(index=False))
    print(summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()
