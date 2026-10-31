"""Summarize fixed-model development sample-size sensitivity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{value:.6f}" if isinstance(value, float) else str(value)
                                       for value in row) + " |")
    return "\n".join(lines)


def report(root: Path, out: Path) -> None:
    cells = sorted(root.glob("*/configuration.json"))
    if len(cells) != 6:
        raise ValueError(f"Expected six completed sample-size cells, found {len(cells)}")
    all_rows = []
    for cfg_path in cells:
        cfg = json.loads(cfg_path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Incomplete or official-test cell: {cfg_path}")
        name = cfg_path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(cfg_path.parent / "metrics.csv")
        if (len(frame) != 30 or set(frame.m) != {2500, 10000, 40000}
            or set(frame.method) != {"size", "constrained"}
            or frame.groupby(["m", "method"]).size().min() != 5
            or frame.invalid_income_rate.max() != 0):
            raise ValueError(f"Bad sample-size table: {cfg_path.parent}")
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", seed)
        frame.insert(2, "cell", name)
        all_rows.append(frame)
    draws = pd.concat(all_rows, ignore_index=True)
    paired = draws.pivot(index=["family", "split_seed", "cell", "m", "replicate"],
                         columns="method", values=["query_linf", "unseen_query_linf"]).reset_index()
    paired.columns = ["_".join(part for part in col if part).strip("_")
                      if isinstance(col, tuple) else col for col in paired.columns]
    paired["delta_query_linf"] = paired.query_linf_constrained - paired.query_linf_size
    paired["delta_unseen_query_linf"] = paired.unseen_query_linf_constrained - paired.unseen_query_linf_size
    by_cell = paired.groupby(["family", "split_seed", "m"], as_index=False).agg(
        size_query_mean=("query_linf_size", "mean"),
        size_query_draw_range=("query_linf_size", lambda x: float(x.max() - x.min())),
        constrained_query_mean=("query_linf_constrained", "mean"),
        delta_query_mean=("delta_query_linf", "mean"),
        delta_query_min_draw=("delta_query_linf", "min"),
        delta_query_max_draw=("delta_query_linf", "max"),
        delta_unseen_mean=("delta_unseen_query_linf", "mean"))
    by_family = by_cell.groupby(["family", "m"], as_index=False).agg(
        size_query_mean=("size_query_mean", "mean"),
        size_query_draw_range_mean=("size_query_draw_range", "mean"),
        constrained_query_mean=("constrained_query_mean", "mean"),
        delta_query_mean=("delta_query_mean", "mean"),
        delta_query_min_seed=("delta_query_mean", "min"),
        delta_query_max_seed=("delta_query_mean", "max"),
        delta_unseen_mean=("delta_unseen_mean", "mean"))
    out.mkdir(parents=True, exist_ok=True)
    draws.to_csv(out / "all_draws.csv", index=False)
    paired.to_csv(out / "paired_draws.csv", index=False)
    by_cell.to_csv(out / "by_cell.csv", index=False)
    by_family.to_csv(out / "by_family.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Projected sample-size development audit", "",
        "Six fixed-model cells; five draws at each m. The 10,000-row observations were reused exactly from the compatible constrained audit. Official Adult test was not evaluated.", "",
        markdown(by_family), "",
        "Negative constrained-minus-size differences favour constrained weighting. The three split seeds reuse Adult people. Draw ranges capture synthetic sampling variation only. Different m values use the same public seeds and can share random-stream prefixes; they are not independent replication units. The real reference is finite and is not population truth.", "",
    ]))
    print(by_family.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()
