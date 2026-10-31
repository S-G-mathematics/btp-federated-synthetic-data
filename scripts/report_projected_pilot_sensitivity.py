"""Report fixed-model synthetic-pilot Monte Carlo sensitivity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from representation_constrained import constrained_query_minimax


def markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{value:.6f}" if isinstance(value, float) else str(value)
                                       for value in row) + " |")
    return "\n".join(lines)


def summarize(root: Path, out: Path) -> None:
    cells = sorted(root.glob("*/configuration.json"))
    if len(cells) != 6:
        raise ValueError(f"Expected six completed pilot cells, found {len(cells)}")
    frames = []
    for path in cells:
        cfg = json.loads(path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"] or not cfg["source_H_reproduced_exactly"]:
            raise ValueError(f"Invalid pilot cell: {path}")
        name = path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        split_seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(path.parent / "metrics.csv")
        if (len(frame) != 20 or set(frame.pilot_per_client) != {500, 1500, 5000, 15000}
            or frame.groupby("pilot_per_client").size().min() != 5
            or frame.fixed_H_ref_validation_excess.min() < -1e-8):
            raise ValueError(f"Incomplete/invalid pilot table: {path.parent}")
        fixed = np.load(path.parent / "fixed_matrices.npz")
        Href, bcal, alpha = fixed["H_reference"], fixed["b_calibration"], fixed["alpha"]
        same_target_oracle, _ = constrained_query_minimax(Href, bcal, alpha, .25, .5)
        same_target_optimum = float(np.max(np.abs(Href @ same_target_oracle - bcal)))
        fits = json.loads((path.parent / "fit_records.json").read_text())
        fits_by_key = {(item["pilot_per_client"], item["replicate"]): item for item in fits}
        same_target_excess = []
        for row in frame.itertuples(index=False):
            fit = fits_by_key[(int(row.pilot_per_client), int(row.replicate))]
            weights = np.asarray(fit["weights"], float)
            value = float(np.max(np.abs(Href @ weights - bcal)))
            if value + 1e-7 < same_target_optimum:
                raise ValueError(f"Same-target finite LP certificate violated: {path.parent}")
            same_target_excess.append(max(0., value - same_target_optimum))
        frame["same_target_fixed_H_ref_excess"] = same_target_excess
        frame["same_target_fixed_H_ref_optimum"] = same_target_optimum
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", split_seed)
        frame.insert(2, "cell", name)
        frames.append(frame)
    draws = pd.concat(frames, ignore_index=True)
    by_cell = draws.groupby(["family", "split_seed", "pilot_per_client"], as_index=False).agg(
        H_error_mean=("pilot_H_max_error_vs_independent_finite_H_ref", "mean"),
        H_error_max=("pilot_H_max_error_vs_independent_finite_H_ref", "max"),
        weight_l1_from_source_mean=("weight_l1_from_source_constrained", "mean"),
        fixed_reference_excess_mean=("fixed_H_ref_validation_excess", "mean"),
        same_target_fixed_reference_excess_mean=("same_target_fixed_H_ref_excess", "mean"),
        fresh_delta_primary_mean=("delta_query_linf", "mean"),
        fresh_delta_primary_min=("delta_query_linf", "min"),
        fresh_delta_primary_max=("delta_query_linf", "max"),
        fresh_delta_unseen_mean=("delta_unseen_query_linf", "mean"))
    by_family = by_cell.groupby(["family", "pilot_per_client"], as_index=False).agg(
        H_error_mean=("H_error_mean", "mean"),
        weight_l1_from_source_mean=("weight_l1_from_source_mean", "mean"),
        fixed_reference_excess_mean=("fixed_reference_excess_mean", "mean"),
        same_target_fixed_reference_excess_mean=("same_target_fixed_reference_excess_mean", "mean"),
        fresh_delta_primary_mean=("fresh_delta_primary_mean", "mean"),
        fresh_delta_primary_min_seed=("fresh_delta_primary_mean", "min"),
        fresh_delta_primary_max_seed=("fresh_delta_primary_mean", "max"),
        fresh_delta_unseen_mean=("fresh_delta_unseen_mean", "mean"))
    out.mkdir(parents=True, exist_ok=True)
    draws.to_csv(out / "all_pilots.csv", index=False)
    by_cell.to_csv(out / "by_cell.csv", index=False)
    by_family.to_csv(out / "by_family.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Projected pilot sensitivity development audit", "",
        "Six cells, four pilot sizes and five independent pilot seeds per size. Saved source H reproduced exactly in every cell. Official Adult test was not evaluated.", "",
        markdown(by_family), "",
        "H_ref is an independent finite synthetic matrix. The same-target finite-H_ref excess uses the same released calibration vector b_cal and isolates synthetic-pilot fitting sensitivity conditional on finite H_ref. The validation LP instead uses real validation b_val and has greater access; its gap also includes a target difference. Neither LP is a population oracle. Fresh-sample primary differences are constrained minus size; negative favours constrained. Split seeds share Adult people and pilot replicates share fitted models.", "",
    ]))
    print(by_family.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.root, args.out)


if __name__ == "__main__":
    main()
