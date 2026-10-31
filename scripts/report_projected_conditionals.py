"""Audit matched direct-teacher versus trained-student conditional results."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.evaluation import CONDITIONS
from btp.privacy import public_schema


def markdown(frame: pd.DataFrame) -> str:
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{x:.6f}" if isinstance(x, float) else str(x) for x in row) + " |")
    return "\n".join(lines)


def report(root: Path, out: Path) -> None:
    cells = sorted(root.glob("*/configuration.json"))
    if len(cells) != 6:
        raise ValueError(f"Expected six completed conditional cells, found {len(cells)}")
    metrics, answers, structural = [], [], []
    condition_by_name = {condition.name: condition for condition in CONDITIONS}
    mapping = public_schema()["education_number_map"]
    for cfg_path in cells:
        cfg = json.loads(cfg_path.read_text())
        if cfg["status"] != "complete" or cfg["official_test_used"]:
            raise ValueError(f"Invalid condition cell: {cfg_path}")
        name = cfg_path.parent.name
        family = "chow_liu_age_k5" if name.startswith("chow_liu_age_k5_") else "mixed_gmm_label_skew_k10"
        seed = int(name.split("_s")[-1].split("_")[0])
        frame = pd.read_csv(cfg_path.parent / "condition_metrics.csv")
        query = pd.read_csv(cfg_path.parent / "condition_query_answers.csv")
        if (set(frame.method) != {"size", "constrained"}
            or set(frame.condition) != set(cfg["condition_names"])):
            raise ValueError(f"Incomplete condition table: {cfg_path.parent}")
        completed = frame.query("status == 'completed'")
        for (method, condition), pair in completed.groupby(["method", "condition"]):
            if (set(pair.route) != {"direct_teacher_rejection", "trained_student_postfilter"}
                or pair.generated_rows_evaluated.nunique() != 1
                or pair.student_postfilter_violation.max() != 0):
                raise ValueError(f"Unmatched route rows or violation: {name}/{method}/{condition}")
        for (method, condition), pair in completed.groupby(["method", "condition"]):
            saved = pd.read_csv(cfg_path.parent / f"accepted_{method}_{condition}.csv.gz")
            expected_rows = int(pair.generated_rows_evaluated.iloc[0])
            known = saved.education.map(mapping)
            mapped = known.notna()
            code_violations = int((saved.loc[mapped, "education-num"].to_numpy()
                                   != known.loc[mapped].to_numpy()).sum())
            condition_violations = int((~np.asarray(condition_by_name[condition].evaluate(saved), bool)).sum())
            if len(saved) != expected_rows or code_violations or condition_violations:
                raise ValueError(f"Saved student support/schema violation: {name}/{method}/{condition}")
            structural.append({"family": family, "split_seed": seed,
                               "method": method, "condition": condition,
                               "saved_rows": len(saved), "mapped_code_violations": code_violations,
                               "postfilter_condition_violations": condition_violations})
        frame.insert(0, "family", family)
        frame.insert(1, "split_seed", seed)
        frame.insert(2, "cell", name)
        query.insert(0, "family", family)
        query.insert(1, "split_seed", seed)
        query.insert(2, "cell", name)
        metrics.append(frame)
        answers.append(query)
    metrics = pd.concat(metrics, ignore_index=True)
    answers = pd.concat(answers, ignore_index=True)
    completed = metrics.query("status == 'completed'").copy()
    paired = completed.pivot(index=["family", "split_seed", "condition", "method"],
                             columns="route", values="conditional_query_linf").reset_index()
    paired["student_minus_direct"] = paired.trained_student_postfilter - paired.direct_teacher_rejection
    summary = paired.groupby(["family", "condition", "method"], as_index=False).agg(
        cells=("split_seed", "nunique"),
        direct_query_linf_mean=("direct_teacher_rejection", "mean"),
        student_query_linf_mean=("trained_student_postfilter", "mean"),
        student_minus_direct_mean=("student_minus_direct", "mean"),
        student_minus_direct_min_seed=("student_minus_direct", "min"),
        student_minus_direct_max_seed=("student_minus_direct", "max"))
    support = metrics.groupby(["family", "condition", "method", "status"], as_index=False).agg(
        rows=("cell", "size"), real_count_min=("real_assessment_condition_count", "min"),
        teacher_matches_min=("teacher_matching_rows", "min"))
    violation = completed.query("route == 'trained_student_postfilter'").groupby(
        ["family", "condition", "method"], as_index=False).agg(
        raw_violation_mean=("student_raw_violation", "mean"),
        matched_rows_mean=("generated_rows_evaluated", "mean"),
        direct_pool_matching_mean=("independent_direct_matching_rows", "mean"))
    out.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out / "all_condition_metrics.csv", index=False)
    answers.to_csv(out / "all_condition_query_answers.csv", index=False)
    paired.to_csv(out / "paired_route_errors.csv", index=False)
    summary.to_csv(out / "route_summary.csv", index=False)
    support.to_csv(out / "support_summary.csv", index=False)
    violation.to_csv(out / "violation_summary.csv", index=False)
    pd.DataFrame(structural).to_csv(out / "saved_student_support_audit.csv", index=False)
    (out / "OVERVIEW.md").write_text("\n".join([
        "# Projected registered-condition development audit", "",
        "Six fixed-model cells; direct rejection uses an independent 30,000-row pool and matches the accepted student row count. Server support is decided from synthetic teacher counts only. Official Adult test was not evaluated.", "",
        "## Route query errors", "", markdown(summary), "",
        "## Support and abstention", "", markdown(support), "",
        "Positive student-minus-direct error favours direct rejection. These students are fitted separately for the four registered conditions; no cross-condition generalization is demonstrated. Three split seeds reuse Adult people.", "",
    ]))
    print(summary.to_string(index=False))
    print(support.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report(args.root, args.out)


if __name__ == "__main__":
    main()
