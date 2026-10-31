"""Summarize the preregistered six-cell development secondary audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    def display(value):
        if isinstance(value, (float, np.floating)):
            return f"{value:.5f}"
        return str(value)
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    lines += ["| " + " | ".join(display(value) for value in row) + " |"
              for row in frame.itertuples(index=False, name=None)]
    return "\n".join(lines)


def summarize(root: Path, out: Path) -> None:
    cells = sorted(path for path in root.iterdir() if (path / "configuration.json").exists())
    if len(cells) != 6:
        raise ValueError(f"Expected exactly six completed secondary cells, found {len(cells)}")
    utility_rows, subgroup_rows = [], []
    for cell in cells:
        config = json.loads((cell / "configuration.json").read_text())
        if config["status"] != "complete" or config["official_test_used"]:
            raise ValueError(f"Invalid assessment role/status: {cell}")
        name = cell.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        seed = int(name.split("_s")[-1].split("_")[0])
        utility = pd.read_csv(cell / "utility_metrics.csv")
        if len(utility) != (5 if family == "chow_liu_age_k5" else 10) * 6 + 6:
            # Three methods x two learners x (one global plus K clients).
            expected = 3 * 2 * (1 + (5 if family == "chow_liu_age_k5" else 10))
            if len(utility) != expected:
                raise ValueError(f"Wrong metric row count: {cell}: {len(utility)} != {expected}")
        subgroup = pd.read_csv(cell / "subgroup_queries.csv")
        if len(subgroup) != 2 * 5 * 17:
            raise ValueError(f"Wrong subgroup row count: {cell}")
        predictions = pd.read_csv(cell / "paired_predictions.csv.gz")
        expected_n = int(utility.query("method == 'size' and learner == 'logistic' and client == 'alpha_global'").n.iloc[0])
        for (method, learner), part in predictions.groupby(["method", "learner"]):
            if len(part) != expected_n or part.row_id.duplicated().any():
                raise ValueError(f"Bad paired prediction row IDs: {cell}: {method}/{learner}")
            if not part.row_id.str.startswith("train:").all():
                raise ValueError(f"Assessment IDs must be development rows: {cell}")
        ids = predictions.query("method == 'size' and learner == 'logistic'")[["row_id", "client", "income_label"]].reset_index(drop=True)
        for (_, _), part in predictions.groupby(["method", "learner"], sort=False):
            if not ids.equals(part[["row_id", "client", "income_label"]].reset_index(drop=True)):
                raise ValueError(f"Predictions not paired: {cell}")
        for learner in ("logistic", "extra_trees"):
            ref = utility.query("learner == @learner and client == 'alpha_global'").set_index("method")
            for method in ("size", "constrained", "TRTR_privileged"):
                entry = {"family": family, "seed": seed, "cell": name, "learner": learner,
                         "method": method, "n_assessment": expected_n}
                for metric in ("auroc", "auprc", "brier", "log_loss", "ece_fixed10", "balanced_accuracy", "f1"):
                    entry[metric] = float(ref.loc[method, metric])
                    entry[f"delta_{metric}_vs_size"] = float(ref.loc[method, metric] - ref.loc["size", metric])
                client = utility.query("learner == @learner and method == @method and client != 'alpha_global'")
                entry["worst_client_auroc"] = float(client.auroc.min())
                entry["worst_client_brier"] = float(client.brier.max())
                utility_rows.append(entry)
        supported = subgroup[subgroup.supported_real_mass_ge_1pct]
        for (method, draw), part in supported.groupby(["method", "draw"]):
            subgroup_rows.append({"family": family, "seed": seed, "cell": name,
                                  "method": method, "draw": int(draw),
                                  "max_supported_abs_error": float(part.abs_error.max()),
                                  "mean_supported_abs_error": float(part.abs_error.mean()),
                                  "supported_queries": len(part)})
    utility = pd.DataFrame(utility_rows)
    subgroup = pd.DataFrame(subgroup_rows)
    per_draw = subgroup.pivot(index=["family", "seed", "cell", "draw"], columns="method",
                              values="max_supported_abs_error").reset_index()
    per_draw["delta_constrained_vs_size"] = per_draw.constrained - per_draw["size"]
    per_cell_subgroup = per_draw.groupby(["family", "seed"], as_index=False).agg(
        size_max_error_mean=("size", "mean"), constrained_max_error_mean=("constrained", "mean"),
        delta_max_error_mean=("delta_constrained_vs_size", "mean"),
        delta_max_error_min=("delta_constrained_vs_size", "min"),
        delta_max_error_max=("delta_constrained_vs_size", "max"))
    summary = utility.query("method == 'constrained'").groupby(["family", "learner"], as_index=False).agg(
        delta_auroc_mean=("delta_auroc_vs_size", "mean"),
        delta_auroc_min=("delta_auroc_vs_size", "min"),
        delta_auroc_max=("delta_auroc_vs_size", "max"),
        delta_brier_mean=("delta_brier_vs_size", "mean"),
        delta_brier_min=("delta_brier_vs_size", "min"),
        delta_brier_max=("delta_brier_vs_size", "max"))
    summary["auroc_noninferior_margin_minus_0p01"] = summary.delta_auroc_mean >= -.01
    subgroup_summary = per_cell_subgroup.groupby("family", as_index=False).agg(
        delta_max_error_mean=("delta_max_error_mean", "mean"),
        delta_max_error_min_seed=("delta_max_error_mean", "min"),
        delta_max_error_max_seed=("delta_max_error_mean", "max"))
    subgroup_summary["subgroup_noninferior_margin_plus_0p01"] = subgroup_summary.delta_max_error_mean <= .01
    out.mkdir(parents=True, exist_ok=True)
    utility.to_csv(out / "utility_global_by_cell.csv", index=False)
    subgroup.to_csv(out / "subgroup_draws.csv", index=False)
    per_cell_subgroup.to_csv(out / "subgroup_by_cell.csv", index=False)
    summary.to_csv(out / "utility_gate_summary.csv", index=False)
    subgroup_summary.to_csv(out / "subgroup_gate_summary.csv", index=False)
    lines = ["# Projected secondary development audit", "",
             "Six registered cells; official Adult test was not evaluated. Three development split seeds reuse people and are not independent cohorts. Five synthetic draws per method/cell measure subgroup sampling variation; one train/tune/calibration draw supplies each predictive fit.", "",
             "## Utility: constrained minus size", "", markdown_table(summary), "",
             "## Supported subgroup maximum prevalence error: constrained minus size", "",
             markdown_table(subgroup_summary), "",
             "Negative differences favour constrained weighting. The privileged real-trained TRTR is a separate diagnostic, not a server release. These are selected exploratory cells, not a global method-selection basis. Raw predictions and all client metrics remain in the cell outputs.", ""]
    (out / "OVERVIEW.md").write_text("\n".join(lines))
    print(summary.to_string(index=False))
    print(subgroup_summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.root, args.out)


if __name__ == "__main__":
    main()
