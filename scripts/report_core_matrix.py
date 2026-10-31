"""Paired development diagnostics for the 54-cell matched core.

This report recomputes the audit-only validation selector from saved per-method
rows. It never chooses a global winner or reads official-test records.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, prepare_splits
from btp.evaluation import public_workloads, weighted_reference
from btp.privacy import public_schema
from btp.run import select_release_method

MANIFEST = ROOT / "reports/core_matrix_audit_20261024/manifest.csv"
OUT = ROOT / "reports/core_matrix_diagnostics_20261024"


def validation_target(cell: Path, cfg: dict, alpha: np.ndarray) -> np.ndarray:
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat(
        [splits[name] for name in ("train", "tune", "calibration", "validation")]
    )
    if not manifest.row_id.isin(development.index).all():
        raise ValueError(f"Manifest mismatch: {cell}")
    joined = manifest.join(development, on="row_id", validate="one_to_one")
    groups = [
        joined[(joined.split == "validation") & (joined.client == i)][
            list(ALL_COLUMNS)
        ].copy()
        for i in range(cfg["k"])
    ]
    workload, _ = public_workloads(public_schema())
    return weighted_reference(groups, workload, alpha)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    eligible = manifest[
        manifest.status.isin(("complete_exact", "reuse_with_selection_bridge"))
    ]
    rows = []
    for item in eligible.itertuples():
        cell = ROOT / item.cell
        cfg = json.loads((cell / "configuration.json").read_text())
        if cfg["reference_role"] != "development_assessment":
            raise ValueError(f"Official test encountered: {cell}")
        validation = pd.read_csv(cell / "exp01_validation.csv")
        assessment = pd.read_csv(cell / "exp01_test.csv")
        selected = select_release_method(validation.to_dict("records"))
        size = assessment[assessment.method == "size"]
        if size.empty:
            raise ValueError(f"Missing size baseline: {cell}")
        size_loss = float(size.query_linf.mean())
        size_audit = float(size.unseen_query_linf.mean())
        saved = np.load(cell / "releases/permitted_summary.npz")
        H, alpha = saved["H"], saved["alpha"]
        b_validation = validation_target(cell, cfg, alpha)
        size_pilot_loss = float(np.max(np.abs(H @ alpha - b_validation)))
        oracle = json.loads((cell / "exp02_oracle.json").read_text())
        if not oracle["solver"]["success"]:
            raise ValueError(f"Oracle LP failed: {cell}")
        oracle_pilot_loss = float(oracle["solver"]["objective"])
        if size_pilot_loss + 1e-6 < oracle_pilot_loss:
            raise ValueError(f"Oracle objective exceeds size pilot loss: {cell}")
        weight_records = {
            x["method"]: x
            for x in json.loads((cell / "weight_fits.json").read_text())["methods"]
            if x.get("success")
        }
        for method, group in assessment.groupby("method"):
            fit = weight_records.get(method)
            if fit is None:
                raise ValueError(f"Missing successful fit for {method}: {cell}")
            w = np.asarray(fit["weights"], float)
            if w.shape != alpha.shape or not np.isclose(w.sum(), 1, atol=1e-6):
                raise ValueError(f"Invalid fitted weights for {method}: {cell}")
            method_validation = validation[validation.method == method]
            if len(method_validation) != 1:
                raise ValueError(f"Missing validation row for {method}: {cell}")
            rows.append({
                "cell": item.cell,
                "generator": item.generator,
                "partition": item.partition,
                "k": item.k,
                "split_seed": item.seed,
                "status": item.status,
                "code_hash": cfg["code_hash"],
                "method": method,
                "access": method_validation.iloc[0]["access"],
                "audit_only_selected_within_cell": method == selected,
                "validation_query_linf": float(method_validation.iloc[0].query_linf),
                "assessment_query_linf_mean": float(group.query_linf.mean()),
                "assessment_query_linf_synthetic_sd": float(group.query_linf.std()),
                "assessment_unseen_query_linf_mean": float(
                    group.unseen_query_linf.mean()
                ),
                "paired_delta_vs_size": float(group.query_linf.mean() - size_loss),
                "audit_delta_vs_size": float(
                    group.unseen_query_linf.mean() - size_audit
                ),
                "synthetic_repeats": len(group),
                "weight_l1_from_alpha": float(np.abs(w - alpha).sum()),
                "minimum_weight_alpha_ratio": float(np.min(w / alpha)),
                "effective_client_count": float(1 / np.sum(w * w)),
                "near_zero_clients": int(np.sum(w < 1e-8)),
                "size_fixed_pilot_validation_loss": size_pilot_loss,
                "oracle_fixed_pilot_validation_loss": oracle_pilot_loss,
                "oracle_headroom_vs_size_fixed_pilot": float(
                    size_pilot_loss - oracle_pilot_loss
                ),
            })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "cell_method_diagnostics.csv", index=False)
    summary = (
        frame.groupby(["generator", "partition", "k", "method"])
        .agg(
            split_seeds=("split_seed", "nunique"),
            primary_delta_mean=("paired_delta_vs_size", "mean"),
            primary_delta_min=("paired_delta_vs_size", "min"),
            primary_delta_max=("paired_delta_vs_size", "max"),
            unseen_audit_delta_mean=("audit_delta_vs_size", "mean"),
            weight_l1_mean=("weight_l1_from_alpha", "mean"),
            oracle_headroom_mean=("oracle_headroom_vs_size_fixed_pilot", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(OUT / "slice_method_summary.csv", index=False)
    policy = frame[frame.audit_only_selected_within_cell]
    policy.to_csv(OUT / "within_cell_policy.csv", index=False)
    print(
        "cells", frame.cell.nunique(),
        "method_rows", len(frame),
        "selected_wins", int((policy.paired_delta_vs_size < 0).sum()),
        "of", len(policy),
    )
    print("Do not infer independent-cohort confidence intervals from Adult split seeds.")


if __name__ == "__main__":
    main()
