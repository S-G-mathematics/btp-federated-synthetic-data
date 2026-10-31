"""Frozen secondary Bank TSTR/TRTR logistic utility comparator."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from btp.evaluation import sample_mixture
from scripts.bank_data import LABEL, MODEL_COLUMNS, SCALES

C_GRID = (.1, 1., 10.)
TRAIN_ROWS = 10000
TUNE_ROWS = 2000
CALIBRATION_ROWS = 2000
CLIP = 1e-6


def features() -> list[str]:
    return [c for c in MODEL_COLUMNS if c != LABEL]


def outcome(frame: pd.DataFrame) -> np.ndarray:
    return (frame[LABEL].to_numpy() == "yes").astype(int)


def fit_predictor(train: pd.DataFrame, tune: pd.DataFrame, calibration: pd.DataFrame,
                  seed: int) -> tuple[object, object, dict]:
    numeric = list(SCALES)
    categorical = [c for c in features() if c not in SCALES]
    if any(outcome(part).min() == outcome(part).max() for part in (train, tune, calibration)):
        raise ValueError("Logistic utility requires two classes in train, tune and calibration")
    trials = []
    winner = None
    for C in C_GRID:
        transform = ColumnTransformer([
            ("numeric", StandardScaler(), numeric),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=True), categorical),
        ])
        clf = make_pipeline(transform, LogisticRegression(C=C, solver="liblinear",
                            max_iter=600, random_state=seed))
        clf.fit(train[features()], outcome(train))
        p = np.clip(clf.predict_proba(tune[features()])[:, 1], CLIP, 1-CLIP)
        loss = float(brier_score_loss(outcome(tune), p))
        trials.append({"C": C, "tune_brier": loss})
        if winner is None or (loss, C) < (winner[0], winner[1]):
            winner = loss, C, clf
    assert winner is not None
    base = winner[2]
    pc = np.clip(base.predict_proba(calibration[features()])[:, 1], CLIP, 1-CLIP)
    logit = np.log(pc / (1-pc)).reshape(-1, 1)
    platt = LogisticRegression(C=1e6, solver="liblinear", max_iter=600,
                               random_state=seed+1).fit(logit, outcome(calibration))
    return base, platt, {"selected_C": winner[1], "trials": trials,
                         "calibration": "Platt sigmoid on separate source-specific set",
                         "calibration_rows": len(calibration), "train_rows": len(train),
                         "tune_rows": len(tune), "clip": CLIP}


def predict(base, platt, frame: pd.DataFrame) -> np.ndarray:
    raw = np.clip(base.predict_proba(frame[features()])[:, 1], CLIP, 1-CLIP)
    transformed = np.log(raw / (1-raw)).reshape(-1, 1)
    return np.clip(platt.predict_proba(transformed)[:, 1], CLIP, 1-CLIP)


def summarize(y: np.ndarray, p: np.ndarray, weights: np.ndarray) -> dict:
    return {"brier": float(brier_score_loss(y, p, sample_weight=weights)),
            "log_loss": float(log_loss(y, p, sample_weight=weights, labels=[0, 1])),
            "auroc": float(roc_auc_score(y, p, sample_weight=weights)) if len(set(y)) == 2 else None,
            "auprc": float(average_precision_score(y, p, sample_weight=weights)) if len(set(y)) == 2 else None}


def evaluate(cell: Path, groups: dict, models: list, weights: dict,
             alpha: np.ndarray, seed: int) -> None:
    assessed = pd.concat(groups["assessment"])
    client_ids = np.concatenate([np.full(len(part), i) for i, part in enumerate(groups["assessment"])])
    row_weights = np.concatenate([np.full(len(part), alpha[i]/len(part))
                                  for i, part in enumerate(groups["assessment"])])
    y = outcome(assessed)
    results = []
    predictions = []
    settings = {}
    for method, w in [("trtr_privileged", None), *weights.items()]:
        if method == "trtr_privileged":
            train, tune, calibration = (pd.concat(groups[name]) for name in
                                        ("train", "tune", "calibration"))
        else:
            train, _ = sample_mixture(models, w, TRAIN_ROWS, seed+9000)
            tune, _ = sample_mixture(models, w, TUNE_ROWS, seed+10000)
            calibration, _ = sample_mixture(models, w, CALIBRATION_ROWS, seed+11000)
        base, platt, record = fit_predictor(train, tune, calibration, seed+12000)
        p = predict(base, platt, assessed)
        metrics = summarize(y, p, row_weights)
        results.append({"method": method, "access": "privileged_real_development" if w is None else
                        "synthetic_released_models", **metrics, "n_assessment": len(assessed)})
        predictions.extend({"row_id": rid, "client": int(i), "y": int(yi),
                            "probability": float(pi), "method": method,
                            "alpha_row_weight": float(wi)}
                           for rid, i, yi, pi, wi in zip(assessed.index, client_ids, y, p, row_weights))
        settings[method] = record
        (cell / f"utility_{method}.pkl").write_bytes(pickle.dumps({"base": base, "platt": platt}))
    pd.DataFrame(results).to_csv(cell / "utility_metrics.csv", index=False)
    pd.DataFrame(predictions).to_csv(cell / "utility_predictions.csv", index=False)
    (cell / "utility_settings.json").write_text(json.dumps(settings, indent=2) + "\n")
