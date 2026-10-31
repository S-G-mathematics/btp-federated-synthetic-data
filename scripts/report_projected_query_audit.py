"""Summarize fixed-query answers by workload, arity and support stratum."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

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
        raise ValueError(f"Expected six completed query cells, found {len(paths)}")
    answers, draws, uncertainty = [], [], []
    for path in paths:
        cfg = json.loads(path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Invalid query cell: {path}")
        name = path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(path.parent / "query_answers.csv")
        draw = pd.read_csv(path.parent / "draw_metrics.csv")
        u = json.loads((path.parent / "uncertainty.json").read_text())
        if (len(frame) != 175 * 2 * 5 or len(draw) != 10
            or set(frame.workload) != {"primary", "unseen_audit"}
            or set(frame.method) != {"size", "constrained"}
            or (draw.query_linf-draw.saved_query_linf).abs().max() > 1e-10
            or u["L_queries_primary_and_audit"] != 175):
            raise ValueError(f"Incomplete/incompatible query table: {path.parent}")
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", seed)
        draw.insert(0, "family", family)
        draw.insert(1, "split_seed", seed)
        answers.append(frame)
        draws.append(draw)
        uncertainty.append({"family": family, "split_seed": seed, **u})
    answers = pd.concat(answers, ignore_index=True)
    draws = pd.concat(draws, ignore_index=True)
    paired = answers.pivot(index=["family", "split_seed", "replicate", "workload", "query",
                                  "arity", "support_stratum", "real_alpha_answer"],
                           columns="method", values="absolute_error").reset_index()
    paired["constrained_minus_size_abs_error"] = paired.constrained - paired["size"]
    strata = paired.groupby(["family", "workload", "arity", "support_stratum"], as_index=False).agg(
        query_draw_rows=("query", "size"),
        distinct_queries=("query", "nunique"),
        size_abs_error_mean=("size", "mean"),
        constrained_abs_error_mean=("constrained", "mean"),
        constrained_minus_size_mean=("constrained_minus_size_abs_error", "mean"),
        size_abs_error_max=("size", "max"),
        constrained_abs_error_max=("constrained", "max"))
    maxima = answers.loc[answers.groupby(["family", "split_seed", "method", "replicate",
                                           "workload"]).absolute_error.idxmax()].copy()
    dominating = maxima.groupby(["family", "method", "workload", "query"], as_index=False).agg(
        maximum_times=("query", "size"),
        mean_dominant_error=("absolute_error", "mean"))
    dominating = dominating.sort_values(["family", "method", "workload", "maximum_times"],
                                        ascending=[True, True, True, False])
    targets = answers.drop_duplicates(["family", "split_seed", "workload", "query"]).copy()
    targets["alpha_vs_pooled_gap"] = (targets.real_alpha_answer-
                                      targets.real_unweighted_pooled_answer_secondary).abs()
    target_gap = targets.groupby(["family", "split_seed", "workload"], as_index=False).agg(
        alpha_vs_pooled_query_linf=("alpha_vs_pooled_gap", "max"))
    draw_summary = draws.groupby(["family", "method"], as_index=False).agg(
        primary_query_linf_mean=("query_linf", "mean"),
        primary_query_linf_min_draw=("query_linf", "min"),
        primary_query_linf_max_draw=("query_linf", "max"))
    out.mkdir(parents=True, exist_ok=True)
    answers.to_csv(out / "all_query_answers.csv", index=False)
    paired.to_csv(out / "paired_query_errors.csv", index=False)
    strata.to_csv(out / "arity_support_summary.csv", index=False)
    dominating.to_csv(out / "dominant_queries.csv", index=False)
    target_gap.to_csv(out / "alpha_vs_pooled_target_gap.csv", index=False)
    draw_summary.to_csv(out / "draw_summary.csv", index=False)
    pd.DataFrame(uncertainty).to_csv(out / "conditional_uncertainty.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Projected query-level development audit", "",
        "Six fixed-model cells, two weight rules and five exactly reproduced 10,000-row draws each. All 175 registered primary/audit answers are saved; the unweighted pooled real target is secondary. Official Adult test was not evaluated.", "",
        "## Query arity and alpha-support strata", "", markdown(strata), "",
        "## Primary draw maxima", "", markdown(draw_summary), "",
        "The simultaneous radius in conditional_uncertainty.csv follows a Hoeffding/union calculation under independent bounded real and synthetic sampling. Its assumptions are not verified for the Adult records or overlapping splits; it is not a measured population-TV distance or a validated confidence interval. The audit workload has been inspected during development and is not independent confirmation.", "",
    ]))
    print(strata.to_string(index=False))
    print(draw_summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()
