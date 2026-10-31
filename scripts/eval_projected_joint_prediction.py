"""Exact/approximate joint-implied income predictor on paired development people."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from btp.data import PREDICTORS, prepare_splits
from btp.run import code_hash
from eval_projected_secondary import probability_metrics

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
SECONDARY = ROOT / "results/projected_secondary_20261024"
OUTPUT = ROOT / "results/projected_joint_prediction_20261025"


def joint_ratio(models: list, weights: np.ndarray, features: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    labels = ("<=50K", ">50K")
    label_masses = []
    for income in labels:
        frame = features.copy()
        frame["income"] = income
        scores = np.column_stack([model.log_prob(frame) for model in models])
        if np.isnan(scores).any() or np.isposinf(scores).any():
            raise ValueError("Local model emitted invalid joint score")
        label_masses.append(logsumexp(scores + np.log(weights), axis=1))
    denominator = np.logaddexp(*label_masses)
    probability = np.full(len(features), np.nan)
    reason = np.full(len(features), "covered", dtype=object)
    missing = np.isneginf(label_masses[0]) & np.isneginf(label_masses[1])
    reason[missing] = "both_labels_zero_mass"
    other_invalid = ~np.isfinite(denominator) & ~missing
    reason[other_invalid] = "nonfinite_denominator"
    covered = ~(missing | other_invalid)
    probability[covered] = np.exp(label_masses[1][covered]-denominator[covered])
    if np.any(~np.isfinite(probability[covered])) or np.any((probability[covered] < 0) | (probability[covered] > 1)):
        raise ValueError("Invalid normalized joint posterior")
    return probability, reason


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def run_cell(cell: Path, out: Path) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Incompatible projected development source")
    secondary_cfg = json.loads((SECONDARY / cell.name / "configuration.json").read_text())
    if (secondary_cfg["source_code_hash"] != cfg["code_hash"]
        or secondary_cfg["official_test_used"]):
        raise ValueError("Incompatible paired secondary predictions")
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    weights_cfg = json.loads((CONSTRAINED / cell.name / "weight_fits.json").read_text())
    vectors = {method: np.asarray(weights_cfg[method]["weights"], float)
               for method in ("size", "constrained")}
    if not np.allclose(vectors["size"], alpha):
        raise ValueError("Size weights differ from declared alpha")
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    score_kinds = {model.likelihood_kind for model in models}
    if len(score_kinds) != 1:
        raise ValueError("Mixed local score kinds")
    score_kind, = score_kinds
    if cfg["generator"] == "chow_liu" and score_kind != "exact_discretized":
        raise ValueError("Chow-Liu score lost exact discrete status")
    if cfg["generator"] == "mixed_gmm" and score_kind == "exact_discretized":
        raise ValueError("GMM score incorrectly labeled exact")
    predictions = pd.read_csv(SECONDARY / cell.name / "paired_predictions.csv.gz",
                              dtype={"row_id": str})
    base = predictions.loc[(predictions.method == "size") &
                           (predictions.learner == "logistic"),
                           ["row_id", "client", "income_label"]].reset_index(drop=True)
    if base.empty or base.row_id.duplicated().any() or not base.row_id.str.startswith("train:").all():
        raise ValueError("Assessment row IDs invalid")
    wide = predictions.pivot(index="row_id", columns=["method", "learner"],
                             values="probability_high_income").reindex(base.row_id)
    expected = {(method, learner) for method in ("size", "constrained", "TRTR_privileged")
                for learner in ("logistic", "extra_trees")}
    if set(wide.columns) != expected or wide.isna().any().any():
        raise ValueError("Secondary predictor pairs incomplete")
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat([splits[key] for key in ("train", "tune", "calibration", "validation")])
    real = development.loc[base.row_id].reset_index(drop=True)
    if not np.array_equal(real.income.eq(">50K").to_numpy(int), base.income_label.to_numpy(int)):
        raise ValueError("Saved labels do not match development records")
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    client_map = manifest.set_index("row_id").client
    if not np.array_equal(client_map.loc[base.row_id].to_numpy(int), base.client.to_numpy(int)):
        raise ValueError("Saved client IDs do not match immutable manifest")
    row_weights = np.zeros(len(base), float)
    for i, mass in enumerate(alpha):
        take = base.client.to_numpy(int) == i
        if not take.any():
            raise ValueError("Empty development-assessment client")
        row_weights[take] = mass / take.sum()
    metric_rows, coverage_rows, paired_rows = [], [], []
    y = base.income_label.to_numpy(int)
    features = real[list(PREDICTORS)]
    for method, vector in vectors.items():
        posterior, reason = joint_ratio(models, vector, features)
        covered = reason == "covered"
        coverage_rows.append({"joint_method": method, "client": "alpha_global",
            "n": len(base), "covered": int(covered.sum()),
            "unweighted_coverage": float(covered.mean()),
            "alpha_weighted_coverage": float(row_weights[covered].sum()),
            "both_labels_zero_mass": int((reason == "both_labels_zero_mass").sum()),
            "nonfinite_denominator": int((reason == "nonfinite_denominator").sum())})
        for i in range(cfg["k"]):
            take = base.client.to_numpy(int) == i
            coverage_rows.append({"joint_method": method, "client": str(i),
                "n": int(take.sum()), "covered": int((take & covered).sum()),
                "unweighted_coverage": float(covered[take].mean()),
                "alpha_weighted_coverage": float(covered[take].mean()),
                "both_labels_zero_mass": int((take & (reason == "both_labels_zero_mass")).sum()),
                "nonfinite_denominator": int((take & (reason == "nonfinite_denominator")).sum())})
        comparators = {
            "joint_implied": posterior,
            "synthetic_logistic": wide[(method, "logistic")].to_numpy(float),
            "synthetic_extra_trees": wide[(method, "extra_trees")].to_numpy(float),
            "TRTR_privileged_logistic": wide[("TRTR_privileged", "logistic")].to_numpy(float),
            "TRTR_privileged_extra_trees": wide[("TRTR_privileged", "extra_trees")].to_numpy(float),
        }
        for predictor, probability in comparators.items():
            if covered.any():
                metric_rows.append({"joint_method": method, "predictor": predictor,
                    "client": "alpha_global", "covered_only": True,
                    **probability_metrics(y[covered], probability[covered], row_weights[covered].copy())})
            for i in range(cfg["k"]):
                take = covered & (base.client.to_numpy(int) == i)
                if take.any():
                    metric_rows.append({"joint_method": method, "predictor": predictor,
                        "client": str(i), "covered_only": True,
                        **probability_metrics(y[take], probability[take], np.ones(take.sum()))})
        paired_rows.append(pd.DataFrame({
            "row_id": base.row_id, "client": base.client, "income_label": y,
            "joint_method": method, "score_kind": score_kind,
            "coverage_reason": reason, "p_joint": posterior,
            "p_synthetic_logistic": comparators["synthetic_logistic"],
            "p_synthetic_extra_trees": comparators["synthetic_extra_trees"],
            "p_TRTR_privileged_logistic": comparators["TRTR_privileged_logistic"],
            "p_TRTR_privileged_extra_trees": comparators["TRTR_privileged_extra_trees"],
        }))
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(metric_rows).to_csv(out / "covered_prediction_metrics.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(out / "coverage.csv", index=False)
    pd.concat(paired_rows, ignore_index=True).to_csv(out / "paired_predictions_evaluator_private.csv.gz",
        index=False, compression={"method": "gzip", "mtime": 0})
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "secondary_predictions_sha256": hashlib.sha256((SECONDARY / cell.name /
            "paired_predictions.csv.gz").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "score_kind": score_kind,
        "posterior_interpretation": "exact fitted integer/discrete joint" if score_kind == "exact_discretized"
            else "normalized approximate mixed-data scores, not exact emitted-row conditional mass",
        "off_support_policy": "abstain, no fallback or smoothing",
        "official_test_used": False, "reference_role": cfg["reference_role"],
        "elapsed_seconds": time.monotonic()-started,
        "ended_utc": datetime.now(timezone.utc).isoformat(), "status": "complete",
    }, indent=2) + "\n")
    print(cell.name, "complete", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cells", type=int, default=6)
    args = parser.parse_args()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease_path = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    targets = [(generator, partition, k, seed)
        for generator, partition, k in (("chow_liu", "age", 5),
                                        ("mixed_gmm", "label_skew", 10))
        for seed in (101, 202, 303)]
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        began, completed = time.monotonic(), 0
        for generator, partition, k, seed in targets:
            if completed >= args.max_cells or time.monotonic()-began >= resources["campaign_wall_seconds"]:
                break
            matches = list(SOURCE.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError("Expected one source cell")
            cell, = matches
            out = OUTPUT / cell.name
            marker = out / "configuration.json"
            if marker.exists():
                prior = json.loads(marker.read_text())
                if (prior.get("status") == "complete" and prior.get("source_code_hash") == code_hash()
                    and prior.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible existing joint result: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior joint failure retained: {out}")
            try:
                capacity(resources)
                run_cell(cell, out)
            except Exception as exc:
                out.mkdir(parents=True, exist_ok=True)
                (out / "failure.json").write_text(json.dumps({
                    "source_cell": str(cell.relative_to(ROOT)),
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "failed_utc": datetime.now(timezone.utc).isoformat(),
                }, indent=2) + "\n")
                raise
            completed += 1
        print("newly_completed", completed)


if __name__ == "__main__":
    main()
