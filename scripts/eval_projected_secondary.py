"""Matched projected subgroup and calibrated downstream-utility development audit.

The statistical generator/weight fitting is complete before this privileged
evaluator reads real assessment rows. This script never uses official test.
"""
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
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, f1_score, log_loss, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from btp.data import NUMERIC, PREDICTORS, prepare_splits
from btp.evaluation import Query, Workload, sample_mixture, weighted_reference
from btp.run import code_hash
from representation_constrained import reference_parts

TRAIN_ROWS = 10000
TUNE_ROWS = 3000
CAL_ROWS = 3000
SUBGROUP_DRAWS = 5
MIN_GROUP_MASS = .01
SUBGROUP_QUERIES = [
    Query("sex_Female", (("sex", "eq", "Female"),)),
    Query("sex_Male", (("sex", "eq", "Male"),)),
    Query("race_White", (("race", "eq", "White"),)),
    Query("race_Black", (("race", "eq", "Black"),)),
    Query("race_Asian", (("race", "eq", "Asian-Pac-Islander"),)),
    Query("education_HS", (("education", "eq", "HS-grad"),)),
    Query("education_Bachelors", (("education", "eq", "Bachelors"),)),
    Query("education_Masters", (("education", "eq", "Masters"),)),
    Query("income_high", (("income", "eq", ">50K"),)),
    Query("age_17_30", (("age", "between", (17, 30)),)),
    Query("age_31_45", (("age", "between", (31, 45)),)),
    Query("age_46_60", (("age", "between", (46, 60)),)),
    Query("age_61_90", (("age", "between", (61, 90)),)),
    Query("Female_income_high", (("sex", "eq", "Female"), ("income", "eq", ">50K"))),
    Query("Male_income_high", (("sex", "eq", "Male"), ("income", "eq", ">50K"))),
    Query("Black_income_high", (("race", "eq", "Black"), ("income", "eq", ">50K"))),
    Query("Bachelors_income_high", (("education", "eq", "Bachelors"), ("income", "eq", ">50K"))),
]


def label(frame: pd.DataFrame) -> np.ndarray:
    return frame.income.eq(">50K").to_numpy(dtype=int)


def feature_transform():
    numeric = [c for c in PREDICTORS if c in NUMERIC]
    categorical = [c for c in PREDICTORS if c not in NUMERIC]
    return ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])


def model_grid(learner: str, seed: int):
    if learner == "logistic":
        return [(f"C={c}", make_pipeline(feature_transform(),
            LogisticRegression(C=c, max_iter=800, random_state=seed)))
            for c in (.1, 1., 10.)]
    if learner == "extra_trees":
        return [(f"min_leaf={leaf}", make_pipeline(feature_transform(),
            ExtraTreesClassifier(n_estimators=100, min_samples_leaf=leaf,
                                 max_features="sqrt", n_jobs=1, random_state=seed)))
            for leaf in (3, 10)]
    raise ValueError(learner)


def tune_and_calibrate(train: pd.DataFrame, tune: pd.DataFrame,
                       calibration: pd.DataFrame, learner: str, seed: int):
    if any(frame.income.nunique() != 2 for frame in (train, tune, calibration)):
        raise ValueError("Training, tuning and calibration each need both income classes")
    trials = []
    best = None
    for setting, model in model_grid(learner, seed):
        began = time.monotonic()
        model.fit(train[list(PREDICTORS)], label(train))
        p = np.clip(model.predict_proba(tune[list(PREDICTORS)])[:, 1], 1e-6, 1-1e-6)
        score = float(brier_score_loss(label(tune), p))
        trials.append({"setting": setting, "synthetic_or_real_tune_brier": score,
                       "fit_seconds": time.monotonic() - began, "status": "complete"})
        if best is None or (score, setting) < (best[0], best[1]):
            best = (score, setting, model)
    assert best is not None
    raw = np.clip(best[2].predict_proba(calibration[list(PREDICTORS)])[:, 1], 1e-6, 1-1e-6)
    logit = np.log(raw / (1 - raw)).reshape(-1, 1)
    calibrator = LogisticRegression(C=1000., max_iter=500, random_state=seed)
    calibrator.fit(logit, label(calibration))
    return best[2], calibrator, best[1], trials


def calibrated_probability(model, calibrator, frame: pd.DataFrame) -> np.ndarray:
    raw = np.clip(model.predict_proba(frame[list(PREDICTORS)])[:, 1], 1e-6, 1-1e-6)
    logit = np.log(raw / (1 - raw)).reshape(-1, 1)
    return np.clip(calibrator.predict_proba(logit)[:, 1], 1e-6, 1-1e-6)


def probability_metrics(y: np.ndarray, p: np.ndarray, weights: np.ndarray) -> dict:
    weights = np.asarray(weights, float)
    weights /= weights.sum()
    y, p = np.asarray(y, int), np.asarray(p, float)
    bins = np.linspace(0, 1, 11)
    ece = 0.
    for low, high in zip(bins[:-1], bins[1:]):
        take = (p >= low) & ((p < high) if high < 1 else (p <= high))
        if take.any():
            ece += weights[take].sum() * abs(np.average(y[take], weights=weights[take])
                                               - np.average(p[take], weights=weights[take]))
    two_classes = len(np.unique(y)) == 2
    return {
        "n": int(len(y)), "positive_count": int(y.sum()),
        "auroc": float(roc_auc_score(y, p, sample_weight=weights)) if two_classes else None,
        "auprc": float(average_precision_score(y, p, sample_weight=weights)) if two_classes else None,
        "brier": float(brier_score_loss(y, p, sample_weight=weights)),
        "log_loss": float(log_loss(y, p, sample_weight=weights, labels=[0, 1])),
        "ece_fixed10": float(ece),
        "balanced_accuracy": float(balanced_accuracy_score(y, p >= .5, sample_weight=weights)) if two_classes else None,
        "f1": float(f1_score(y, p >= .5, sample_weight=weights, zero_division=0)),
    }


def check_capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def run_cell(cell: Path, output: Path) -> None:
    began = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if cfg["reference_role"] != "development_assessment" or cfg["workload_version"] != "projected_v2":
        raise ValueError("Secondary gate accepts projected development cells only")
    if cfg["code_hash"] != code_hash():
        raise ValueError("Local model code hash differs from saved projected checkpoint")
    constrained_root = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
    weights_cfg = json.loads((constrained_root / cell.name / "weight_fits.json").read_text())
    weights = {method: np.asarray(weights_cfg[method]["weights"], float)
               for method in ("size", "constrained")}
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    if not np.allclose(weights["size"], alpha):
        raise ValueError("Size baseline differs from fixed alpha")
    reference = reference_parts(cell, cfg, alpha)["test"]
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    row_ids = np.concatenate([
        manifest.loc[(manifest.split == "test") & (manifest.client == i), "row_id"].to_numpy()
        for i in range(cfg["k"])
    ])
    test = pd.concat(reference)
    clients = np.concatenate([np.full(len(group), i) for i, group in enumerate(reference)])
    row_weights = np.concatenate([np.full(len(group), a / len(group))
                                  for group, a in zip(reference, alpha)])
    if len(test) != len(clients) or len(test) != len(row_weights) or len(test) != len(row_ids):
        raise ValueError("Reference/client alignment mismatch")
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    workload = Workload(SUBGROUP_QUERIES)
    real_query = weighted_reference(reference, workload, alpha)
    real_counts = workload.transform(test).sum(axis=0).astype(int)
    subgroup_rows, metric_rows, prediction_rows, settings_rows = [], [], [], []
    data_sources = {}
    for method, weight in weights.items():
        train, train_counts = sample_mixture(models, weight, TRAIN_ROWS, cfg["seed"] + 11000)
        tune, tune_counts = sample_mixture(models, weight, TUNE_ROWS, cfg["seed"] + 12000)
        calibration, cal_counts = sample_mixture(models, weight, CAL_ROWS, cfg["seed"] + 13000)
        if any(counts.sum() != requested for counts, requested in ((train_counts, TRAIN_ROWS),
            (tune_counts, TUNE_ROWS), (cal_counts, CAL_ROWS))):
            raise RuntimeError("Mixture allocation failed")
        data_sources[method] = (train, tune, calibration)
        for draw in range(SUBGROUP_DRAWS):
            if draw == 0:
                subgroup_frame, subgroup_counts = train, train_counts
            else:
                subgroup_frame, subgroup_counts = sample_mixture(
                    models, weight, TRAIN_ROWS, cfg["seed"] + 11000 + draw)
            if subgroup_counts.sum() != TRAIN_ROWS:
                raise RuntimeError("Subgroup-draw mixture allocation failed")
            synthetic_query = workload.mean(subgroup_frame)
            for q, truth, count, estimate in zip(SUBGROUP_QUERIES, real_query, real_counts, synthetic_query):
                subgroup_rows.append({"method": method, "draw": draw,
                    "draw_seed": cfg["seed"] + 11000 + draw,
                    "query": q.name, "real_alpha_mean": float(truth),
                    "real_assessment_count": int(count),
                    "synthetic_mean": float(estimate), "abs_error": float(abs(estimate - truth)),
                    "supported_real_mass_ge_1pct": bool(truth >= MIN_GROUP_MASS)})
        settings_rows.append({"method": method, "train_seed": cfg["seed"] + 11000,
            "tune_seed": cfg["seed"] + 12000, "calibration_seed": cfg["seed"] + 13000,
            "train_client_counts": train_counts.tolist(), "tune_client_counts": tune_counts.tolist(),
            "calibration_client_counts": cal_counts.tolist(),
            "weight_l1_from_alpha": float(np.abs(weight - alpha).sum())})
    data_sources["TRTR_privileged"] = (splits["train"], splits["tune"], splits["calibration"])
    output.mkdir(parents=True, exist_ok=True)
    for learner in ("logistic", "extra_trees"):
        for method, (train, tune, calibration) in data_sources.items():
            model, calibrator, setting, trials = tune_and_calibrate(
                train, tune, calibration, learner, cfg["seed"])
            p = calibrated_probability(model, calibrator, test)
            metric_rows.append({"method": method, "learner": learner, "client": "alpha_global",
                                **probability_metrics(label(test), p, row_weights.copy())})
            for i in range(cfg["k"]):
                take = clients == i
                metric_rows.append({"method": method, "learner": learner, "client": str(i),
                                    **probability_metrics(label(test)[take], p[take], np.ones(take.sum()))})
            prediction_rows.append(pd.DataFrame({"row_id": row_ids,
                "client": clients, "income_label": label(test),
                "probability_high_income": p, "method": method, "learner": learner}))
            settings_rows.append({"method": method, "learner": learner,
                "selected_setting": setting, "tuning_trials": trials,
                "calibration": "Platt logistic on separate source-matched calibration draw",
                "privileged_real_training": method == "TRTR_privileged"})
            model_dir = output / ("evaluator_private" if method == "TRTR_privileged"
                                  else "synthetic_predictors")
            model_dir.mkdir(parents=True, exist_ok=True)
            with (model_dir / f"model_{method}_{learner}.pkl").open("wb") as handle:
                pickle.dump({"predictor": model, "calibrator": calibrator}, handle)
    pd.DataFrame(subgroup_rows).to_csv(output / "subgroup_queries.csv", index=False)
    pd.DataFrame(metric_rows).to_csv(output / "utility_metrics.csv", index=False)
    pd.concat(prediction_rows, ignore_index=True).to_csv(output / "paired_predictions.csv.gz",
        index=False, compression={"method": "gzip", "mtime": 0})
    (output / "settings.json").write_text(json.dumps(settings_rows, indent=2) + "\n")
    (output / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)), "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "official_test_used": False, "reference_role": cfg["reference_role"],
        "methods": ["size", "constrained", "TRTR_privileged"],
        "learners": ["logistic", "extra_trees"],
        "synthetic_train_rows": TRAIN_ROWS, "synthetic_tune_rows": TUNE_ROWS,
        "synthetic_calibration_rows": CAL_ROWS, "subgroup_min_real_mass": MIN_GROUP_MASS,
        "independent_subgroup_draws": SUBGROUP_DRAWS,
        "elapsed_seconds": time.monotonic() - began,
        "ended_utc": datetime.now(timezone.utc).isoformat(), "status": "complete",
    }, indent=2) + "\n")
    print(cell.name, "complete", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT / "results/ec2_projected_v2_deterministic_20261024")
    ap.add_argument("--out", type=Path, default=ROOT / "results/projected_secondary_20261024")
    ap.add_argument("--max-cells", type=int, default=6)
    args = ap.parse_args()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease_path = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    targets = [(generator, partition, k, seed)
        for generator, partition, k in (("chow_liu", "age", 5), ("mixed_gmm", "label_skew", 10))
        for seed in (101, 202, 303)]
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        started = time.monotonic()
        completed = 0
        for generator, partition, k, seed in targets:
            if completed >= args.max_cells or time.monotonic() - started >= resources["campaign_wall_seconds"]:
                break
            matches = list(args.root.glob(f"{generator}_{partition}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError(f"Expected one compatible cell for {generator}/{partition}/K{k}/seed{seed}")
            cell = matches[0]
            output = args.out / cell.name
            marker = output / "configuration.json"
            if marker.exists():
                prior = json.loads(marker.read_text())
                if (prior.get("status") == "complete" and prior.get("source_code_hash") == code_hash()
                    and prior.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                    and prior.get("source_manifest_sha256")
                    == hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible existing secondary output: {output}")
            if (output / "failure.json").exists():
                raise RuntimeError(f"Prior failure retained: {output / 'failure.json'}")
            check_capacity(resources)
            try:
                run_cell(cell, output)
            except Exception as exc:
                output.mkdir(parents=True, exist_ok=True)
                (output / "failure.json").write_text(json.dumps({
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
