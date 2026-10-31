"""Validation-only global family selection from corrected projected checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, prepare_splits
from btp.evaluation import sample_mixture, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from scripts.representation_constrained import check_capacity
import yaml

FAMILIES = ("copula", "chow_liu", "mixed_gmm")
PARTITIONS = ("age", "age_education", "label_skew")
SEEDS = (101, 202, 303)
KS = (5, 10)
REPEATS = 5
N_ROWS = 10000
SOURCE_CODE_HASH = "25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868"


def validation_parts(cell: Path, cfg: dict, cache: dict) -> list[pd.DataFrame]:
    seed = int(cfg["seed"])
    if seed not in cache:
        split = prepare_splits(ROOT / "data/raw", seed)
        cache[seed] = pd.concat([split[n] for n in ("train", "tune", "calibration", "validation")])
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    if manifest.row_id.duplicated().any() or not manifest.row_id.isin(cache[seed].index).all():
        raise ValueError(f"Invalid development row manifest: {cell}")
    joined = manifest.join(cache[seed], on="row_id", validate="one_to_one")
    parts = [joined[(joined.split == "validation") & (joined.client == i)][list(ALL_COLUMNS)].copy()
             for i in range(cfg["k"])]
    if any(len(part) == 0 for part in parts):
        raise ValueError(f"Alpha-positive client has no validation rows: {cell}")
    return parts


def selected_fit_seconds(cell: Path, k: int) -> float:
    seconds = []
    for i in range(k):
        fit = json.loads((cell / "client_private" / f"tuning_{i}.json").read_text())
        selected = [t for t in fit["trials"] if t["parameters"] == fit["selected"] and t["status"] == "eligible"]
        if len(selected) != 1 or not np.isfinite(selected[0]["wall_seconds"]):
            raise ValueError(f"Selected local trial missing/invalid: {cell}/client_{i}")
        seconds.append(float(selected[0]["wall_seconds"]))
    return float(sum(seconds))


def run(source: Path, out: Path) -> None:
    started = time.monotonic()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    check_capacity(resources)
    workload, _ = projected_workloads_v2(public_schema())
    definition = json.dumps(workload.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    cells = sorted(p for p in source.iterdir() if p.is_dir())
    expected = {(f, p, k, s) for f in FAMILIES for p in PARTITIONS for k in KS for s in SEEDS}
    actual = set()
    controls = 0
    draws = []
    cell_rows = []
    split_cache = {}
    for cell in cells:
        cfg = json.loads((cell / "configuration.json").read_text())
        key = (cfg["generator"], cfg["partition"], cfg["k"], cfg["seed"])
        if cfg["generator"] == "independent":
            controls += 1
            continue
        if key not in expected or key in actual:
            raise ValueError(f"Unexpected or duplicate core cell: {cell}")
        actual.add(key)
        if cfg["code_hash"] != SOURCE_CODE_HASH or cfg["workload_version"] != "projected_v2" or cfg["reference_role"] != "development_assessment":
            raise ValueError(f"Incompatible source cell: {cell}")
        declared = json.loads((cell / "workloads.json").read_text())
        if declared["calibration"] != json.loads(json.dumps(workload.to_dict())):
            raise ValueError(f"Workload changed: {cell}")
        alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
        if len(alpha) != cfg["k"] or np.min(alpha) <= 0 or not np.isclose(alpha.sum(), 1):
            raise ValueError(f"Invalid target mass: {cell}")
        parts = validation_parts(cell, cfg, split_cache)
        target = weighted_reference(parts, workload, alpha)
        checkpoints = [cell / "releases" / f"client_{i}.pkl" for i in range(cfg["k"])]
        models = [pickle.loads(p.read_bytes()) for p in checkpoints]
        prior = pd.read_csv(cell / "exp01_validation.csv")
        saved_size = prior.loc[prior.method == "size"]
        if len(saved_size) != 1:
            raise ValueError(f"No unique prior size result: {cell}")
        values = []
        for rep in range(REPEATS):
            sample_seed = int(cfg["seed"]) + 4200 + rep
            synth, counts = sample_mixture(models, alpha, N_ROWS, sample_seed)
            if counts.sum() != N_ROWS or not synth.income.isin(["<=50K", ">50K"]).all():
                raise ValueError(f"Invalid synthetic support or allocation: {cell} rep{rep}")
            loss = float(np.max(np.abs(workload.mean(synth) - target)))
            if rep == 0 and abs(loss - float(saved_size.iloc[0].query_linf)) > 1e-10:
                raise ValueError(f"Saved first validation draw does not reproduce: {cell}")
            values.append(loss)
            draws.append({"cell": str(cell.relative_to(ROOT)), "generator": key[0], "partition": key[1],
                          "k": key[2], "seed": key[3], "replicate": rep, "sample_seed": sample_seed,
                          "query_linf": loss, "n_synthetic": N_ROWS, "counts": json.dumps(counts.tolist())})
        cell_rows.append({"cell": str(cell.relative_to(ROOT)), "generator": key[0], "partition": key[1],
                          "k": key[2], "seed": key[3], "query_linf_mean": float(np.mean(values)),
                          "model_bytes": sum(p.stat().st_size for p in checkpoints),
                          "selected_fit_seconds": selected_fit_seconds(cell, cfg["k"]),
                          "source_code_hash": cfg["code_hash"]})
        print(f"validated {len(cell_rows)}/54 {key}", flush=True)
        if time.monotonic() - started > 3600:
            raise TimeoutError("Integrity/selection phase reached its one-hour ceiling")
    if actual != expected:
        raise ValueError(f"Missing core cells: {sorted(expected - actual)}")
    if controls != 3:
        raise ValueError(f"Expected three separate independent controls, observed {controls}")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(draws).to_csv(out / "global_generator_validation_draws.csv", index=False)
    pd.DataFrame(cell_rows).to_csv(out / "global_generator_validation_cells.csv", index=False)
    frame = pd.DataFrame(cell_rows)
    summary = frame.groupby("generator", as_index=False).agg(
        mean_validation_query_linf=("query_linf_mean", "mean"),
        median_model_bytes=("model_bytes", "median"),
        median_selected_fit_seconds=("selected_fit_seconds", "median"),
        cells=("cell", "count"),
    )
    minimum = float(summary.mean_validation_query_linf.min())
    summary["within_0p001_tie"] = summary.mean_validation_query_linf <= minimum + .001 + 1e-12
    tied = summary.loc[summary.within_0p001_tie].sort_values(
        ["median_model_bytes", "median_selected_fit_seconds", "generator"], kind="stable")
    selected = str(tied.iloc[0].generator)
    summary["selected"] = summary.generator.eq(selected)
    summary.to_csv(out / "global_generator_validation_selection.csv", index=False)
    artifact = out / "global_generator_validation_selection.csv"
    (out / "decision.json").write_text(json.dumps({
        "selected_generator": selected, "candidate_families": list(FAMILIES),
        "runner_up_by_validation_mean": str(summary.sort_values(["mean_validation_query_linf", "generator"]).loc[
            lambda x: x.generator.ne(selected)].iloc[0].generator),
        "selection_table_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "primary_workload_sha256": hashlib.sha256(definition).hexdigest(),
        "source_code_hash": SOURCE_CODE_HASH, "cell_count": len(cell_rows), "draw_count": len(draws),
        "test_used_for_selection": False, "assessment_used_for_selection": False,
        "elapsed_seconds": time.monotonic() - started, "finished_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(summary.to_string(index=False), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(ROOT / args.source, ROOT / args.out)


if __name__ == "__main__":
    main()
