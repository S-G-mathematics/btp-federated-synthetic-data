"""Registered fixed-quantity, two-severity Adult mechanism contrast."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import NUMERIC, _stable_uniform, prepare_splits
from btp.evaluation import empirical_metrics, sample_mixture, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash, tune_client
from scripts.representation_constrained import constrained_query_minimax

OUT = ROOT / "results/severity_fixed_quantity_20261025"
REPORT = ROOT / "reports/mechanisms"
SEEDS = (711, 722, 733)
SEVERITIES = (.25, .85)
K = 5
TRAIN_PER_CLIENT = 1000
TUNE_PER_CLIENT = 200
M = 10000
REPEATS = 5


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def split_development(seed: int) -> dict[str, pd.DataFrame]:
    splits = prepare_splits(ROOT / "data/raw", seed)
    validation = splits["validation"]
    mask = np.asarray([int.from_bytes(hashlib.sha256(repr(tuple(row)).encode()).digest()[:8], "big") % 2 == 0
                       for row in validation.itertuples(index=False, name=None)])
    splits["validation"] = validation.loc[mask].copy()
    splits["assessment"] = validation.loc[~mask].copy()
    del splits["test"]  # Official Adult test is never an endpoint here.
    del splits["quarantine"]
    return splits


def age_edges(train: pd.DataFrame) -> tuple[float, ...]:
    return tuple(float(v) for v in np.unique(np.quantile(train.age, [.2, .4, .6, .8])))


def age_base_probabilities(frame: pd.DataFrame, edges: tuple[float, ...]) -> np.ndarray:
    age_bin = np.searchsorted(np.asarray(edges), frame.age.to_numpy(), side="right")
    n_bins = len(edges) + 1
    centers = np.linspace(0, n_bins - 1, K)
    score = age_bin.astype(float)
    logits = -(score[:, None] / max(n_bins-1, 1) - centers[None, :] / max(K-1, 1))**2
    temperature = max(.02, (1.01-.8)*.8 + .02)
    logits /= temperature
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    return probs / probs.sum(axis=1, keepdims=True)


def assign(frame: pd.DataFrame, edges: tuple[float, ...], severity: float,
           seed: int) -> np.ndarray:
    base = age_base_probabilities(frame, edges)
    probs = (1-severity)/K + severity*base
    uniforms = np.asarray([_stable_uniform(rid, seed) for rid in frame.index])
    return np.asarray([min(K-1, int(np.searchsorted(np.cumsum(p), u, side="right")))
                       for p, u in zip(probs, uniforms)], int)


def groups_for_seed(splits: dict, seed: int) -> tuple[dict[float, dict], tuple[float, ...]]:
    edges = age_edges(splits["train"])
    outputs = {}
    for severity in SEVERITIES:
        groups = {}
        for split, frame in splits.items():
            ids = assign(frame, edges, severity, seed)
            groups[split] = [frame.iloc[np.flatnonzero(ids == i)].copy() for i in range(K)]
        outputs[severity] = groups
    return outputs, edges


def subsample(groups: dict, seed: int) -> dict:
    result = {name: [part.copy() for part in collection] for name, collection in groups.items()}
    for name, n in (("train", TRAIN_PER_CLIENT), ("tune", TUNE_PER_CLIENT)):
        for i, part in enumerate(result[name]):
            if len(part) < n:
                raise ValueError(f"Client {i} has {len(part)} {name} rows, below fixed {n}")
            result[name][i] = part.sample(n=n, random_state=seed + 10000*i + (0 if name=="train" else 1)).sort_index()
    return result


def preflight(seed: int) -> tuple[dict, dict, tuple]:
    splits = split_development(seed)
    all_groups, edges = groups_for_seed(splits, seed)
    minimum = {str(severity): {split: min(map(len, all_groups[severity][split]))
                               for split in ("train", "tune", "calibration", "validation", "assessment")}
               for severity in SEVERITIES}
    for severity in SEVERITIES:
        gr = all_groups[severity]
        if min(map(len, gr["train"])) < TRAIN_PER_CLIENT or min(map(len, gr["tune"])) < TUNE_PER_CLIENT:
            raise ValueError(f"Paired severity contrast unsupported for seed{seed}: {minimum}")
        if any(len(part) == 0 for split in ("calibration", "validation", "assessment") for part in gr[split]):
            raise ValueError(f"Paired severity reference unsupported for seed{seed}: {minimum}")
    return all_groups, minimum, edges


def run_cell(seed: int, severity: float, groups: dict, minimum: dict, edges: tuple) -> None:
    started = time.monotonic()
    cell = OUT / f"copula_age_k5_s{seed}_severity{str(severity).replace('.', 'p')}"
    cell.mkdir(parents=True, exist_ok=True)
    if (cell / "complete.json").is_file():
        return
    groups = subsample(groups, seed)
    alpha = np.ones(K)/K
    schema = public_schema()
    workload, audit = projected_workloads_v2(schema)
    cfg = {"seed": seed, "severity": severity, "generator": "copula", "k": K,
           "train_per_client": TRAIN_PER_CLIENT, "tune_per_client": TUNE_PER_CLIENT,
           "alpha": alpha.tolist(), "age_edges_training_only": edges,
           "source_code_hash": code_hash(), "raw_sha256": sha(ROOT / "data/raw/adult.zip"),
           "reference_role": "development_assessment", "created_at_utc": utc()}
    write_json(cell / "configuration.json", cfg)
    manifests = []
    for split, collection in groups.items():
        for i, part in enumerate(collection):
            manifests.extend({"row_id": rid, "split": split, "client": i} for rid in part.index)
    pd.DataFrame(manifests).to_csv(cell / "partition_manifest.csv", index=False)
    write_json(cell / "achieved_assignment.json", {"minimum_before_subsampling": minimum,
               "train_age_means": [float(g.age.mean()) for g in groups["train"]],
               "train_education_num_means": [float(g["education-num"].mean()) for g in groups["train"]],
               "counts_after_subsampling": {s: [len(p) for p in col] for s, col in groups.items()}})
    models = []
    local_scores = []
    for i in range(K):
        checkpoint = cell / f"client_{i}.pkl"
        if checkpoint.is_file() and (cell / f"tuning_{i}.json").is_file():
            model = pickle.loads(checkpoint.read_bytes())
            tune = json.loads((cell / f"tuning_{i}.json").read_text())
        else:
            model, selected, trials = tune_client("copula", groups["train"][i],
                groups["tune"][i], workload, schema, seed+100000*i,
                {"smoke": False, "tune_samples": 1000, "structural_projection": True})
            tune = {"selected": selected, "trials": trials}
            write_json(cell / f"tuning_{i}.json", tune)
            checkpoint.write_bytes(pickle.dumps(model))
        selected = [t for t in tune["trials"] if t.get("parameters") == tune["selected"]
                    and t.get("status") == "eligible"]
        if len(selected) != 1:
            raise ValueError("Invalid selected local tuning record")
        local_scores.append(float(selected[0]["local_tune_query_mae"]))
        models.append(model)
        if time.monotonic() - started > 3600:
            raise TimeoutError("Severity cell fitting exceeded one-hour cap")
    H = np.column_stack([workload.mean(model.sample(1500, seed+3000+i*1009))
                         for i, model in enumerate(models)])
    b_cal = weighted_reference(groups["calibration"], workload, alpha)
    np.savez_compressed(cell / "permitted_summary.npz", H=H, b_calibration=b_cal, alpha=alpha)
    constrained, cert = constrained_query_minimax(H, b_cal, alpha, .25, .5)
    b_val = weighted_reference(groups["validation"], workload, alpha)
    oracle, oracle_cert = constrained_query_minimax(H, b_val, alpha, 2., 0.)
    write_json(cell / "weight_fits.json", {"size": alpha.tolist(),
               "constrained": constrained.tolist(), "constrained_certificate": cert,
               "fixed_pilot_validation_oracle": {"weights": oracle.tolist(), **oracle_cert},
               "local_tune_mae": local_scores})
    rows = []
    for name, w in (("size", alpha), ("constrained", constrained)):
        for rep in range(REPEATS):
            draw_seed = seed+5200+rep
            synth, counts = sample_mixture(models, w, M, draw_seed)
            metrics = empirical_metrics(groups["assessment"], synth, workload, audit, alpha)
            rows.append({"seed": seed, "severity": severity, "method": name,
                         "replicate": rep, "draw_seed": draw_seed,
                         "allocation_counts": json.dumps(counts.tolist()),
                         "weight_l1": float(np.abs(w-alpha).sum()), **metrics})
    pd.DataFrame(rows).to_csv(cell / "metrics.csv", index=False)
    write_json(cell / "complete.json", {"status": "complete", "elapsed_seconds": time.monotonic()-started,
               "finished_at_utc": utc(), "metrics_sha256": sha(cell / "metrics.csv")})


def run() -> None:
    resource = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease = Path(os.path.expanduser(resource["shared_compute_lease"]))
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    manifest = [{"generator": "copula", "k": K, "seed": seed, "severity": severity,
                 "train_size_per_client": TRAIN_PER_CLIENT, "tune_size_per_client": TUNE_PER_CLIENT}
                for seed in SEEDS for severity in SEVERITIES]
    path = REPORT / "severity_cell_manifest.json"
    if path.exists() and json.loads(path.read_text())["cells"] != manifest:
        raise ValueError("Severity manifest changed")
    if not path.exists():
        write_json(path, {"created_at_utc": utc(), "cells": manifest})
    started = time.monotonic()
    with lease.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for seed in SEEDS:
            memory = Path("/proc/meminfo").read_text()
            available = next(int(line.split()[1])*1024 for line in memory.splitlines() if line.startswith("MemAvailable:"))
            if available < resource["minimum_available_ram_gib"]*2**30 or shutil.disk_usage(ROOT).free < resource["minimum_free_disk_gib"]*2**30:
                raise RuntimeError("Shared capacity reserve breached")
            try:
                all_groups, minimum, edges = preflight(seed)
            except Exception as exc:
                for severity in SEVERITIES:
                    cell = OUT / f"copula_age_k5_s{seed}_severity{str(severity).replace('.', 'p')}"
                    write_json(cell / "unsupported.json", {"status": "unsupported_pair", "reason": str(exc)})
                print(seed, "unsupported pair", flush=True)
                continue
            for severity in SEVERITIES:
                if time.monotonic()-started > resource["campaign_wall_seconds"]:
                    raise TimeoutError("Severity invocation reached two-hour limit")
                try:
                    run_cell(seed, severity, all_groups[severity], minimum, edges)
                    print(seed, severity, "complete", flush=True)
                except Exception:
                    cell = OUT / f"copula_age_k5_s{seed}_severity{str(severity).replace('.', 'p')}"
                    write_json(cell / "failure.json", {"status": "failed", "traceback": traceback.format_exc()})
                    raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", required=True)
    ap.parse_args()
    run()


if __name__ == "__main__":
    main()
