"""Rebuildable gate over the corrected projected Adult development evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.projection import EducationNumberProjection
from btp.run import code_hash
from scripts.freeze_gate import validate_freeze

EXPECTED_HASH = "25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868"
EXPECTED_ZIP = "6a1768af20e87be9b7be6548f153208a463d28bff7687890b912e4b9bb99f30e"
GENERATORS = ("chow_liu", "copula", "mixed_gmm")
PARTITIONS = ("age", "age_education", "label_skew")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(core: Path, constrained: Path, rebuilt: Path, out: Path) -> dict:
    current_hash = code_hash()
    # Historical development checkpoints were fitted under EXPECTED_HASH.
    # The later, official-confirmation source is separately frozen and may
    # differ; validate it rather than pretending it is the original source.
    freeze = validate_freeze(ROOT / "SELECTION_FROZEN.json", ROOT, current_hash)
    if freeze["software"]["code_hash"] != current_hash:
        raise ValueError("Current source differs from the accepted confirmation freeze")
    zip_path = ROOT.parent / "BTP_EC2_Complete_Handoff_20261024.zip"
    if not zip_path.is_file():
        zip_path = ROOT.parent / "ORIGINAL_HANDOFF" / zip_path.name
    if sha(zip_path) != EXPECTED_ZIP:
        raise ValueError("Preserved original ZIP hash differs")
    manifest = pd.read_csv(rebuilt / "manifest.csv")
    if len(manifest) != 57 or set(manifest.code_hash) != {EXPECTED_HASH}:
        raise ValueError("Corrected core manifest must have 57 matching-hash cells")
    observed = {(r.generator, r.partition, int(r.k), int(r.seed)) for r in manifest.itertuples()}
    expected = {(g, p, k, seed) for g in GENERATORS for p in PARTITIONS
                for k in (5, 10) for seed in (101, 202, 303)}
    controls = observed - expected
    if not expected <= observed or len(controls) != 3 or any(g != "independent" for g, _, _, _ in controls):
        raise ValueError("54-cell registered grid or three controls are incomplete")
    split_hashes: dict[tuple, set[str]] = defaultdict(set)
    workload_hashes: set[str] = set()
    records = []
    for row in manifest.itertuples():
        cell = ROOT / row.cell
        cfg = json.loads((cell / "configuration.json").read_text())
        if (cfg["reference_role"] != "development_assessment"
            or cfg["workload_version"] != "projected_v2"
            or cfg["code_hash"] != EXPECTED_HASH
            or cfg["profile"]["repeats"] != 5):
            raise ValueError(f"Incompatible current cell {cell}")
        parts = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
        if (len(parts) != 32536 or not parts.row_id.is_unique
            or parts.row_id.str.startswith("test:").any()
            or set(parts.split) != {"train", "tune", "calibration", "validation", "test"}):
            raise ValueError(f"Development split/official-test boundary failed: {cell}")
        split_hash = sha(cell / "partition_manifest.csv")
        split_hashes[(row.partition, int(row.k), int(row.seed))].add(split_hash)
        workload_hashes.add(sha(cell / "workloads.json"))
        partition = json.loads((cell / "partition.json").read_text())
        counts = np.asarray(partition["counts"], int)
        alpha = np.asarray(partition["alpha"], float)
        if len(counts) != row.k or len(alpha) != row.k or not np.allclose(alpha, counts/counts.sum()):
            raise ValueError(f"Target alpha/counts mismatch: {cell}")
        oracle = json.loads((cell / "exp02_oracle.json").read_text())
        solver = oracle["solver"]
        if (not solver["success"] or not solver["details"]["simplex_valid"]
            or abs(solver["objective"] - solver["details"]["residual_linf"]) > 1e-7):
            raise ValueError(f"Fixed-pilot LP certificate invalid: {cell}")
        validation = pd.read_csv(cell / "exp01_validation.csv")
        assessment = pd.read_csv(cell / "exp01_test.csv")
        if (len(validation) != 13 or len(assessment) != 65
            or assessment.groupby("method").replicate.nunique().ne(5).any()
            or assessment.n_synthetic.ne(10000).any()
            or assessment.invalid_income_rate.gt(0).any()):
            raise ValueError(f"Method/draw/support count mismatch: {cell}")
        selection = json.loads((cell / "selection_frozen.json").read_text())
        if selection["audit_used_for_selection"] or selection["test_used"]:
            raise ValueError(f"Audit/test used in per-cell validation selection: {cell}")
        fitted = constrained / cell.name
        ccfg = json.loads((fitted / "configuration.json").read_text())
        if (ccfg["source_code_hash"] != EXPECTED_HASH or ccfg["official_test_used"]
            or ccfg["source_manifest_sha256"] != split_hash or ccfg["assessment_repeats"] != 5):
            raise ValueError(f"Incompatible constrained result: {fitted}")
        weights = json.loads((fitted / "weight_fits.json").read_text())
        cw = np.asarray(weights["constrained"]["weights"], float)
        if (not weights["constrained"]["success"] or not np.allclose(weights["size"]["weights"], alpha)
            or abs(cw.sum()-1) > 1e-7 or np.any(cw < .5*alpha-1e-7)
            or np.abs(cw-alpha).sum() > .25+1e-7):
            raise ValueError(f"Representation constraint failed: {fitted}")
        metrics = pd.read_csv(fitted / "metrics.csv")
        a = metrics.loc[metrics.split == "development_assessment"]
        if a.groupby("method").replicate.nunique().to_dict() != {"constrained": 5, "size": 5, "unconstrained": 5}:
            raise ValueError(f"Constrained assessment repeats incomplete: {fitted}")
        records.append({"cell": str(cell.relative_to(ROOT)), "generator": row.generator,
                        "partition": row.partition, "k": int(row.k), "seed": int(row.seed),
                        "split_sha256": split_hash, "workload_sha256": sha(cell / "workloads.json"),
                        "oracle_objective": solver["objective"], "method_rows": len(validation),
                        "assessment_draw_rows": len(assessment),
                        "constrained_l1": float(np.abs(cw-alpha).sum()), "status": "complete"})
    if len(workload_hashes) != 1 or any(len(hashes) != 1 for hashes in split_hashes.values()):
        raise ValueError("Workload or matched generator split identities differ")
    overview = json.loads((rebuilt / "overview.json").read_text())
    cview = json.loads((ROOT / "reports/completion_constrained_rebuild_20261025/overview.json").read_text())
    if (overview["core_only"]["cells"] != 54 or cview["development_cells"] != 57
        or cview["constrained_practical_mean_gain_slices"] != 0
        or not np.isclose(cview["constrained_core"]["mean_paired_delta_vs_size"], .0024279025866620666, atol=1e-12)):
        raise ValueError("Headline core decision did not reproduce")
    exact = next(row for row in manifest.itertuples() if row.generator == "chow_liu")
    exact_cell = ROOT / exact.cell
    model = pickle.loads((exact_cell / "releases/client_0.pkl").read_bytes())
    if not isinstance(model, EducationNumberProjection) or model.likelihood_kind != "exact_discretized":
        raise ValueError("Expected exact projected Chow-Liu checkpoint")
    sample = model.sample(48, 19025)
    known = sample.education.isin(model.mapping)
    projected = sample.loc[known].head(12).copy()
    if projected.empty:
        raise ValueError("No mapped education rows in exact-model spot check")
    lo, hi = model.integer_support
    terms = []
    for value in range(lo, hi+1):
        trial = projected.copy()
        trial["education-num"] = value
        terms.append(model.raw_model.log_prob(trial))
    direct = logsumexp(np.vstack(terms), axis=0)
    np.testing.assert_allclose(model.log_prob(projected), direct, atol=1e-10)
    wrong = projected.copy()
    wrong["education-num"] = np.where(projected["education-num"].to_numpy() == lo, hi, lo)
    if not np.isneginf(model.log_prob(wrong)).all():
        raise ValueError("Projected off-map rows retain nonzero mass")
    result = {"status": "passed", "official_test_scored": False,
              "original_zip_sha256": EXPECTED_ZIP, "adult_zip_sha256": sha(ROOT / "data/raw/adult.zip"),
              "model_code_hash": EXPECTED_HASH,
              "current_frozen_scoring_code_hash": current_hash,
              "historical_checkpoint_replayed_under_later_source": current_hash != EXPECTED_HASH,
              "cells": len(manifest), "core_cells": 54,
              "independent_control_cells": 3, "method_rows": int(sum(x["method_rows"] for x in records)),
              "assessment_draw_rows": int(sum(x["assessment_draw_rows"] for x in records)),
              "certified_fixed_pilot_lps": len(records), "workload_sha256": next(iter(workload_hashes)),
              "matched_split_groups": len(split_hashes),
              "constrained_practical_gain_slices": 0,
              "constrained_core_mean_delta": cview["constrained_core"]["mean_paired_delta_vs_size"],
              "exact_projection_spotcheck": {"cell": exact.cell, "rows": len(projected),
                  "preimages_per_row": hi-lo+1, "off_map_zero": True}}
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(out / "cell_checks.csv", index=False)
    (out / "integrity_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", type=Path, default=ROOT / "results/ec2_projected_v2_deterministic_20261024")
    ap.add_argument("--constrained", type=Path, default=ROOT / "results/representation_constrained_projected_v2_deterministic_20261024")
    ap.add_argument("--rebuilt", type=Path, default=ROOT / "reports/completion_core_rebuild_20261025")
    ap.add_argument("--out", type=Path, default=ROOT / "reports/completion_integrity_20261025")
    args = ap.parse_args()
    audit(args.core, args.constrained, args.rebuilt, args.out)


if __name__ == "__main__":
    main()
