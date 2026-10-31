"""Audit fixed representation constraints on projected version-2 cells."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    cells = pd.read_csv(args.manifest)
    records = []
    for item in cells.itertuples():
        source = args.source / Path(item.cell).name
        cfg = json.loads((source / "configuration.json").read_text())
        assert cfg["status"] == "complete" and not cfg["official_test_used"]
        assert cfg["workload_version"] == "projected_v2"
        assert cfg["source_cell"] == item.cell
        assert cfg["assessment_repeats"] == 5
        fits = json.loads((source / "weight_fits.json").read_text())
        assert fits["constrained"]["success"]
        assert fits["constrained"]["actual_weight_l1"] <= .25 + 1e-7
        assert fits["constrained"]["minimum_weight_alpha_ratio"] >= .5 - 1e-7
        assessment = pd.read_csv(source / "metrics.csv")
        assessment = assessment.loc[assessment.split == "development_assessment"]
        assert assessment.groupby("method").size().to_dict() == {
            "size": 5, "constrained": 5, "unconstrained": 5
        }
        size = assessment.loc[assessment.method == "size"].sort_values("replicate")
        for method, group in assessment.groupby("method"):
            group = group.sort_values("replicate")
            assert group.replicate.tolist() == size.replicate.tolist()
            records.append({
                "cell": item.cell, "generator": item.generator,
                "partition": item.partition, "k": item.k, "seed": item.seed,
                "method": method, "query_linf_mean": float(group.query_linf.mean()),
                "size_query_linf_mean": float(size.query_linf.mean()),
                "paired_delta_vs_size": float((group.query_linf.to_numpy() - size.query_linf.to_numpy()).mean()),
                "audit_delta_vs_size": float((group.unseen_query_linf.to_numpy() - size.unseen_query_linf.to_numpy()).mean()),
                "weight_l1_from_alpha": float(group.weight_l1_from_alpha.iloc[0]),
                "minimum_weight_alpha_ratio": float(group.minimum_weight_alpha_ratio.iloc[0]),
                "alpha_vs_pooled_reference_query_linf": cfg["assessment_target_gap_query_linf"],
                "practical_gain": bool(group.query_linf.mean() - size.query_linf.mean() <= -.005),
                "audit_guardrail": bool(group.unseen_query_linf.mean() - size.unseen_query_linf.mean() <= .005),
            })
    args.out.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records)
    frame.to_csv(args.out / "cell_method_means.csv", index=False)
    slices = (frame.groupby(["generator", "partition", "k", "method"])
        .agg(split_seeds=("seed", "nunique"),
             mean_paired_delta=("paired_delta_vs_size", "mean"),
             min_paired_delta=("paired_delta_vs_size", "min"),
             max_paired_delta=("paired_delta_vs_size", "max"),
             mean_audit_delta=("audit_delta_vs_size", "mean"),
             mean_weight_l1=("weight_l1_from_alpha", "mean"))
        .reset_index())
    slices["practical_mean_gain"] = slices.mean_paired_delta.le(-.005)
    slices["audit_guardrail"] = slices.mean_audit_delta.le(.005)
    slices.to_csv(args.out / "slice_summary.csv", index=False)
    constrained = frame.loc[frame.method == "constrained"]
    def summarize(group):
        return {
            "cells": int(len(group)),
            "practical_gain_cells": int(group.practical_gain.sum()),
            "practical_and_audit_pass_cells": int((group.practical_gain & group.audit_guardrail).sum()),
            "mean_paired_delta_vs_size": float(group.paired_delta_vs_size.mean()),
            "mean_weight_l1_from_alpha": float(group.weight_l1_from_alpha.mean()),
        }
    overview = {
        "development_cells": len(cells), "synthetic_draws_per_method": 5,
        "constrained_all": summarize(constrained),
        "constrained_core": summarize(constrained.loc[constrained.generator.isin(["chow_liu", "copula", "mixed_gmm"])]),
        "constrained_by_generator": {name: summarize(group) for name, group in constrained.groupby("generator")},
        "constrained_practical_mean_gain_slices": int(slices.loc[slices.method.eq("constrained"), "practical_mean_gain"].sum()),
        "constrained_practical_and_audit_slices": int((slices.loc[slices.method.eq("constrained"), "practical_mean_gain"]
            & slices.loc[slices.method.eq("constrained"), "audit_guardrail"]).sum()),
        "development_split_seeds": sorted(int(seed) for seed in cells.seed.unique()),
        "official_test_used": False,
        "scope": "overlapping Adult split seeds; descriptive development assessment, not global selection",
    }
    (args.out / "overview.json").write_text(json.dumps(overview, indent=2) + "\n")
    print(json.dumps(overview, indent=2))


if __name__ == "__main__":
    main()
