"""Deterministic Bank report builder from frozen per-cell artifacts only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "EXTERNAL_PROTOCOL_FROZEN.json"
RESULTS = ROOT / "results/external_bank_20261025"
OUT = ROOT / "reports/external_replication"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    frozen = json.loads(FREEZE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    metric_rows, utility_rows, query_rows, statuses = [], [], [], []
    for spec in frozen["cells"]:
        cell = RESULTS / f'{spec["generator"]}_{spec["partition"]}_k5_s{spec["seed"]}'
        done = cell / "complete.json"
        if not done.is_file():
            fail = json.loads((cell / "failure.json").read_text()) if (cell / "failure.json").is_file() else {}
            statuses.append({**spec, "status": fail.get("status", "not_complete"),
                             "failure": fail.get("traceback", "")})
            continue
        completed = json.loads(done.read_text())
        for name, key in (("metrics.csv", "metrics_sha256"),
                          ("query_answers.csv", "query_answers_sha256"),
                          ("utility_metrics.csv", "utility_metrics_sha256"),
                          ("utility_predictions.csv", "utility_predictions_sha256")):
            if sha(cell / name) != completed[key]:
                raise ValueError(f"Tampered/incompatible cell output: {cell / name}")
        metrics = pd.read_csv(cell / "metrics.csv")
        utility = pd.read_csv(cell / "utility_metrics.csv")
        queries = pd.read_csv(cell / "query_answers.csv")
        if len(metrics) != 15 or metrics.groupby("method").replicate.nunique().ne(5).any():
            raise ValueError(f"Incomplete five-draw comparison: {cell}")
        metric_rows.append(metrics)
        utility_rows.append(utility.assign(**spec))
        query_rows.append(queries.assign(**spec))
        statuses.append({**spec, "status": "complete", "failure": ""})
    pd.DataFrame(statuses).to_csv(OUT / "cell_status.csv", index=False)
    if not metric_rows:
        raise ValueError("No completed frozen external cells")
    metrics = pd.concat(metric_rows, ignore_index=True)
    utilities = pd.concat(utility_rows, ignore_index=True)
    queries = pd.concat(query_rows, ignore_index=True)
    metrics.to_csv(OUT / "all_draws.csv", index=False)
    utilities.to_csv(OUT / "all_utility_metrics.csv", index=False)
    queries.to_csv(OUT / "all_query_answers.csv", index=False)
    cell = metrics.groupby(["generator", "partition", "k", "seed", "method"], as_index=False).agg(
        query_linf_mean=("query_linf", "mean"), query_mae_mean=("query_mae", "mean"),
        audit_linf_mean=("audit_query_linf", "mean"),
        invalid_support_count=("invalid_support_count", "sum"),
        weight_l1=("weight_l1_from_alpha", "first"),
        minimum_weight_ratio=("minimum_weight_alpha_ratio", "first"))
    cell.to_csv(OUT / "cell_means.csv", index=False)
    paired = cell.pivot(index=["generator", "partition", "k", "seed"], columns="method",
                        values="query_linf_mean")
    paired["constrained_minus_size"] = paired["constrained_query_minimax"] - paired["size"]
    paired = paired.reset_index()
    paired.to_csv(OUT / "paired_differences.csv", index=False)
    slices = paired.groupby(["generator", "partition"], as_index=False).agg(
        seeds=("seed", "count"), mean_constrained_minus_size=("constrained_minus_size", "mean"),
        mean_size_loss=("size", "mean"), mean_constrained_loss=("constrained_query_minimax", "mean"))
    slices["practical_gain"] = slices.mean_constrained_minus_size <= -.005
    slices.to_csv(OUT / "slice_decisions.csv", index=False)
    top_queries = queries.loc[queries.workload == "primary"].sort_values(
        "absolute_error", ascending=False).groupby(["generator", "partition", "seed", "method", "replicate"]).head(1)
    top_queries.to_csv(OUT / "worst_primary_queries.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    labels = [f"{r.generator}\n{r.partition}" for r in slices.itertuples()]
    x = np.arange(len(slices))
    ax.bar(x, slices.mean_constrained_minus_size, color=["#1f77b4" if v < 0 else "#c44e52"
                                                            for v in slices.mean_constrained_minus_size])
    ax.axhline(-.005, color="black", linestyle="--", linewidth=1, label="registered practical margin")
    ax.axhline(0, color="gray", linewidth=.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Mean constrained minus size query-max")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "slice_differences.png", dpi=180)
    plt.close(fig)
    summary = {"freeze_sha256": sha(FREEZE), "complete_cells": int(sum(s["status"] == "complete" for s in statuses)),
               "failed_or_missing_cells": int(sum(s["status"] != "complete" for s in statuses)),
               "primary_practical_gain_slices": int(slices.practical_gain.sum()),
               "constrained_minus_size_overall_mean_cell": float(paired.constrained_minus_size.mean()),
               "independent_population_replicates_claimed": False,
               "assessment_used_to_change_adult_selection": False}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
