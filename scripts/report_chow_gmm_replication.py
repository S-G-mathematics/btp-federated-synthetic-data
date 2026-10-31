"""Summarize matched Chow-Liu and mixed-GMM development assessments."""

from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/ec2_chow_gmm_replication_20261024"
OUT = ROOT / "reports/chow_gmm_replication_20261024"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cell in sorted(SOURCE.iterdir()):
        if not (cell / "configuration.json").exists():
            continue
        config = json.loads((cell / "configuration.json").read_text())
        if config["reference_role"] != "development_assessment":
            raise ValueError(f"Unexpected official-test reference: {cell}")
        if not (cell / "exp02_complete.json").exists():
            raise ValueError(f"Incomplete oracle stage: {cell}")
        oracle = json.loads((cell / "exp02_oracle.json").read_text())
        if not oracle["solver"]["success"]:
            raise ValueError(f"Oracle solver failed: {cell}")
        validation = pd.read_csv(cell / "exp01_validation.csv").set_index("method")
        assessment = pd.read_csv(cell / "exp01_test.csv")
        winner = json.loads((cell / "STATUS.json").read_text())["winner_validation"]
        for method, group in assessment.groupby("method"):
            rows.append(
                dict(
                    cell=cell.name,
                    generator=config["generator"],
                    partition=config["partition"],
                    k=config["k"],
                    split_seed=config["seed"],
                    code_hash=config["code_hash"],
                    method=method,
                    selected_within_cell=method == winner,
                    validation_query_linf=float(validation.loc[method, "query_linf"]),
                    assessment_query_linf_seed_mean=float(group.query_linf.mean()),
                    synthetic_repeats=len(group),
                )
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "cell_method_seed_means.csv", index=False)
    size = frame[frame.method == "size"][
        ["cell", "assessment_query_linf_seed_mean"]
    ].rename(columns={"assessment_query_linf_seed_mean": "size_assessment"})
    policy = frame[frame.selected_within_cell].merge(size, on="cell", validate="one_to_one")
    policy["policy_minus_size"] = (
        policy.assessment_query_linf_seed_mean - policy.size_assessment
    )
    policy.to_csv(OUT / "within_cell_validation_policy.csv", index=False)
    summary = (
        frame.groupby(["generator", "k", "method"])
        .agg(
            split_seeds=("split_seed", "nunique"),
            mean_assessment_query_linf=("assessment_query_linf_seed_mean", "mean"),
            sd_over_split_seeds=("assessment_query_linf_seed_mean", "std"),
        )
        .reset_index()
    )
    summary.to_csv(OUT / "method_split_seed_summary.csv", index=False)
    print(
        "cells", frame.cell.nunique(), "method_rows", len(frame),
        "oracle_success", frame.cell.nunique(), "code_hashes", frame.code_hash.nunique()
    )
    print(
        "policy_better_than_size", int((policy.policy_minus_size < 0).sum()),
        "of", len(policy), "mean_diff", round(policy.policy_minus_size.mean(), 6)
    )


if __name__ == "__main__":
    main()
