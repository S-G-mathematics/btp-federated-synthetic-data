"""Paired descriptive audit of version-2 projected development Exp 1/2 cells."""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP
from btp.projection import EducationNumberProjection


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    records, manifest = [], []
    for root in args.roots:
        for cell in sorted(p for p in root.iterdir() if p.is_dir()):
            cfg = json.loads((cell / "configuration.json").read_text())
            assert cfg["workload_version"] == "projected_v2"
            assert cfg["reference_role"] == "development_assessment"
            assert cfg["profile"]["repeats"] == 5
            assert (cell / "exp01_complete.json").exists()
            assert (cell / "exp02_complete.json").exists()
            release = json.loads((cell / "releases/release_contract.json").read_text())
            assert release["public_education_number_map"] == PUBLIC_EDUCATION_NUMBER_MAP
            assert release["formal_dp"] is False
            checkpoints = sorted((cell / "releases").glob("client_*.pkl"))
            assert len(checkpoints) == cfg["k"]
            models = [pickle.loads(p.read_bytes()) for p in checkpoints]
            assert all(isinstance(m, EducationNumberProjection) for m in models)
            tune_records = [json.loads((cell / "client_private" / f"tuning_{i}.json").read_text())
                            for i in range(cfg["k"])]
            for model, tuning in zip(models, tune_records):
                assert any(t.get("parameters") == tuning["selected"]
                           and t.get("status") == "eligible"
                           and t.get("finite_tune_score_fraction") == 1.0
                           for t in tuning["trials"])
                raw = model.raw_model
                if hasattr(raw, "gmm"):
                    assert raw.gmm.converged_
                elif hasattr(raw, "converged"):
                    assert raw.converged
            fit = json.loads((cell / "weight_fits.json").read_text())
            fit_by_name = {r["method"]: r for r in fit["methods"]}
            selected = json.loads((cell / "selection_frozen.json").read_text())
            assert not selected["audit_used_for_selection"] and not selected["test_used"]
            alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
            exp1 = pd.read_csv(cell / "exp01_test.csv")
            assert exp1.groupby("method").replicate.nunique().eq(5).all()
            size = exp1.loc[exp1.method == "size"]
            assert len(size) == 5
            synth = pd.read_csv(cell / "synthetic_selected.csv.gz")
            code = synth.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
            known = code.notna()
            mismatches = int(synth.loc[known, "education-num"].ne(code.loc[known]).sum())
            assert mismatches == 0 and len(synth) == 10000
            oracle = json.loads((cell / "exp02_oracle.json").read_text())
            assert oracle["solver"]["success"]
            manifest.append({
                "cell": str(cell), "generator": cfg["generator"], "partition": cfg["partition"],
                "k": cfg["k"], "seed": cfg["seed"], "code_hash": cfg["code_hash"],
                "selected_within_cell": selected["method"], "method_rows": len(fit_by_name),
                "failed_weight_fits": ";".join(n for n,r in fit_by_name.items() if not r["success"]),
                "oracle_lp_success": True, "mapped_mismatches_selected": mismatches,
                "unmapped_rows_selected": int((~known).sum()),
                "exact_score": all(m.likelihood_kind == "exact_discretized" for m in models),
                "released_model_bytes": sum(p.stat().st_size for p in checkpoints),
                "summary_bytes": (cell / "releases/permitted_summary.npz").stat().st_size,
                "failed_local_tune_trials": sum(t.get("status") == "failed"
                    for record in tune_records for t in record["trials"]),
                "nonconverged_or_invalid_tune_trials": sum(t.get("status") == "nonconverged_or_invalid"
                    for record in tune_records for t in record["trials"]),
            })
            for method, rows in exp1.groupby("method"):
                if method not in fit_by_name:
                    weight_l1 = np.nan  # finite-support operator row
                    min_ratio = np.nan
                    access = "finite_support_operator"
                else:
                    f = fit_by_name[method]
                    w = np.asarray(f["weights"], float)
                    weight_l1 = float(np.abs(w - alpha).sum())
                    min_ratio = float(np.min(w / alpha))
                    access = f["access"]
                paired = rows.sort_values("replicate")
                baseline = size.sort_values("replicate")
                assert paired.replicate.tolist() == baseline.replicate.tolist()
                records.append({
                    "cell": str(cell), "generator": cfg["generator"],
                    "partition": cfg["partition"], "k": cfg["k"], "seed": cfg["seed"],
                    "method": method, "access": access, "selected_within_cell": method == selected["method"],
                    "query_linf_mean": float(paired.query_linf.mean()),
                    "size_query_linf_mean": float(baseline.query_linf.mean()),
                    "delta_vs_size_mean": float((paired.query_linf.to_numpy() - baseline.query_linf.to_numpy()).mean()),
                    "audit_delta_vs_size_mean": float((paired.unseen_query_linf.to_numpy() - baseline.unseen_query_linf.to_numpy()).mean()),
                    "weight_l1_from_alpha": weight_l1,
                    "minimum_weight_alpha_ratio": min_ratio,
                })
    if not manifest:
        raise ValueError("No projected cells found")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(manifest).to_csv(out / "manifest.csv", index=False)
    table = pd.DataFrame(records)
    table.to_csv(out / "method_cell_means.csv", index=False)
    table.loc[table.selected_within_cell | table.method.eq("size")].to_csv(out / "selected_vs_size.csv", index=False)
    chosen = table.loc[table.selected_within_cell]
    slice_summary = (chosen.groupby(["generator", "partition", "k"])
        .agg(split_seeds=("seed", "nunique"),
             mean_paired_delta=("delta_vs_size_mean", "mean"),
             min_paired_delta=("delta_vs_size_mean", "min"),
             max_paired_delta=("delta_vs_size_mean", "max"),
             mean_audit_delta=("audit_delta_vs_size_mean", "mean"),
             mean_weight_l1=("weight_l1_from_alpha", "mean"))
        .reset_index())
    slice_summary["practical_mean_gain"] = slice_summary.mean_paired_delta.le(-.005)
    slice_summary["audit_guardrail"] = slice_summary.mean_audit_delta.le(.005)
    slice_summary.to_csv(out / "selected_slice_summary.csv", index=False)
    core = chosen.loc[chosen.generator.isin(["chow_liu", "copula", "mixed_gmm"])]
    def summarize(group):
        return {
            "cells": int(len(group)),
            "size_selected": int(group.method.eq("size").sum()),
            "selected_assessment_wins": int(group.delta_vs_size_mean.lt(0).sum()),
            "selected_practical_gain_cells": int(group.delta_vs_size_mean.le(-.005).sum()),
            "selected_material_harm_cells": int(group.delta_vs_size_mean.gt(.005).sum()),
            "mean_selected_delta_vs_size": float(group.delta_vs_size_mean.mean()),
            "selected_meets_l1_and_floor": int((group.weight_l1_from_alpha.le(.25 + 1e-7)
                & group.minimum_weight_alpha_ratio.ge(.5 - 1e-7)).sum()),
        }
    overview = {
        "all": summarize(chosen), "core_only": summarize(core),
        "by_generator": {name: summarize(group) for name, group in chosen.groupby("generator")},
        "source_code_hashes": sorted({r["code_hash"] for r in manifest}),
        "development_split_seeds": sorted({int(r["seed"]) for r in manifest}),
        "failed_weight_fit_cells": int(sum(bool(r["failed_weight_fits"]) for r in manifest)),
        "failed_local_tune_trials": int(sum(r["failed_local_tune_trials"] for r in manifest)),
        "nonconverged_or_invalid_tune_trials": int(sum(r["nonconverged_or_invalid_tune_trials"] for r in manifest)),
        "core_selected_practical_mean_gain_slices": int(slice_summary.loc[
            slice_summary.generator.isin(["chow_liu", "copula", "mixed_gmm"]),
            "practical_mean_gain"].sum()),
        "core_selected_practical_and_audit_slices": int((slice_summary.loc[
            slice_summary.generator.isin(["chow_liu", "copula", "mixed_gmm"]),
            "practical_mean_gain"] & slice_summary.loc[
            slice_summary.generator.isin(["chow_liu", "copula", "mixed_gmm"]),
            "audit_guardrail"]).sum()),
        "official_test_used": False,
        "scope": "overlapping Adult split seeds, development assessment only; no global selection",
    }
    (out / "overview.json").write_text(json.dumps(overview, indent=2) + "\n")
    print(f"Audited {len(manifest)} projected development cells, {len(records)} method rows; code hashes: {set(r['code_hash'] for r in manifest)}")


if __name__ == "__main__":
    main()
