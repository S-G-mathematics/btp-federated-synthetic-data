"""Aggregate empirical finite-query transfer and student/direct accounting."""
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
        raise ValueError(f"Expected six completed transfer cells, found {len(paths)}")
    bounds, queries, triangles = [], [], []
    for path in paths:
        cfg = json.loads(path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Invalid transfer cell: {path}")
        name = path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        seed = int(name.split("_s")[-1].split("_")[0])
        b = pd.read_csv(path.parent / "condition_bounds.csv")
        q = pd.read_csv(path.parent / "teacher_query_answers.csv")
        t = pd.read_csv(path.parent / "student_teacher_triangles.csv")
        if (len(b) != 8 or set(b.method) != {"size", "constrained"}
            or len(b.loc[b.support_status == "abstain"]) != 2
            or not (b.observed_conditional_linf <= b.empirical_ratio_bound + 1e-10).all()
            or (t.student_real_error > t.triangle_upper_bound + 1e-10).any()):
            raise ValueError(f"Incomplete transfer cell: {path.parent}")
        for frame in (b, q, t):
            frame.insert(0, "family", family)
            frame.insert(1, "split_seed", seed)
        bounds.append(b)
        queries.append(q)
        triangles.append(t)
    bounds = pd.concat(bounds, ignore_index=True)
    queries = pd.concat(queries, ignore_index=True)
    triangles = pd.concat(triangles, ignore_index=True)
    summary = bounds.groupby(["family", "method", "condition", "support_status"], as_index=False).agg(
        cells=("split_seed", "nunique"), real_mass_mean=("real_alpha_mass", "mean"),
        teacher_mass_mean=("synthetic_teacher_mass", "mean"),
        teacher_count_min=("synthetic_teacher_count", "min"),
        observed_conditional_linf_mean=("observed_conditional_linf", "mean"),
        empirical_ratio_bound_mean=("empirical_ratio_bound", "mean"),
        bound_minus_observed_mean=("bound_minus_observed", "mean"))
    triangle_summary = triangles.groupby(["family", "method", "condition"], as_index=False).agg(
        query_rows=("query", "size"),
        student_real_abs_mean=("student_real_error", "mean"),
        direct_real_abs_mean=("direct_real_error", "mean"),
        student_direct_abs_mean=("student_direct_discrepancy", "mean"),
        student_real_abs_max=("student_real_error", "max"),
        direct_real_abs_max=("direct_real_error", "max"))
    out.mkdir(parents=True, exist_ok=True)
    bounds.to_csv(out / "all_condition_bounds.csv", index=False)
    queries.to_csv(out / "all_teacher_query_answers.csv", index=False)
    triangles.to_csv(out / "all_student_teacher_triangles.csv", index=False)
    summary.to_csv(out / "support_bound_summary.csv", index=False)
    triangle_summary.to_csv(out / "student_direct_summary.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Fixed development conditional transfer audit", "",
        "Six projected model cells, two fixed weights, four registered conditions, 30,000-row reconstructed teacher per method/cell. Official Adult test was not used.", "",
        "## Empirical ratio bounds by real support", "", markdown(summary), "",
        "## Matched-row independent direct teacher versus postfiltered student", "", markdown(triangle_summary), "",
        "The bound is deterministic for finite empirical measures and declared queries, conditional on positive real and teacher support. Rare-condition rows remain operational abstentions even when a mathematical ratio is computed. The direct teacher uses an independent synthetic pool; the student/direct term includes sampling noise. Adult split seeds overlap, and this is not population-TV estimation or arbitrary-condition generalization.", "",
    ]))
    print(summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()
