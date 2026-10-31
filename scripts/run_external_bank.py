"""Frozen, sequential Bank Marketing replication with saved cell artifacts."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import platform
import shutil
import subprocess
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
from btp.evaluation import sample_mixture, weighted_reference
from btp.models import fit_model
from scripts.bank_data import (LABEL, MODEL_COLUMNS, SCALES, SOURCE_URL, _group_split,
                               fetch_archive, fit_partition_rule, read_bank)
from scripts.bank_workload import workload_bytes, workload_hash, workloads
from scripts.bank_utility import evaluate as evaluate_utility
from scripts.representation_constrained import constrained_query_minimax

DATA = ROOT / "data/external_bank"
RESULTS = ROOT / "results/external_bank_20261025"
REPORTS = ROOT / "reports/external_replication"
FREEZE = ROOT / "EXTERNAL_PROTOCOL_FROZEN.json"
FAMILIES = ("copula", "chow_liu")
PARTITIONS = ("age_education", "label_skew")
SEEDS = (611, 622, 633)
N_SYNTH = 10000
REPEATS = 5
PILOT_PER_CLIENT = 5000
TUNE_SAMPLE = 1000


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def scoring_sources() -> dict[str, str]:
    paths = [ROOT / "scripts" / name for name in
             ("bank_data.py", "bank_workload.py", "bank_utility.py", "run_external_bank.py",
              "representation_constrained.py")]
    paths += sorted((ROOT / "btp").glob("*.py"))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def rebuild_allowed_parts() -> tuple[dict[str, pd.DataFrame], dict]:
    source = fetch_archive(DATA / "bank_marketing_uci.zip")
    frame = read_bank(source["csv_bytes"])
    return _group_split(frame), source


def prepare_freeze() -> dict:
    if FREEZE.exists():
        return validate_freeze()
    if not (DATA / "data_manifest.json").is_file() or not (DATA / "schema.json").is_file():
        raise ValueError("Run bank_data.py source/split preparation before freeze")
    selection = json.loads((ROOT / "reports/completion_selection_20261025/decision.json").read_text())
    if selection["selected_generator"] != "copula" or selection["runner_up_by_validation_mean"] != "chow_liu":
        raise ValueError("External family set must follow Adult validation-only decision")
    parts, source = rebuild_allowed_parts()
    schema = json.loads((DATA / "schema.json").read_text())
    primary, audit = workloads(parts["train"], schema)
    query_path = DATA / "workloads.json"
    query_path.write_bytes(workload_bytes(primary, audit))
    cells = [{"generator": g, "partition": p, "k": 5, "seed": s}
             for g in FAMILIES for p in PARTITIONS for s in SEEDS]
    freeze = {
        "project": "IIT Guwahati BTP external Bank Marketing replication",
        "protocol_version": "external_bank_v1_20261025", "created_at_utc": utc(),
        "dataset": "official UCI bank-additional-full.csv, duration excluded",
        "source_url": SOURCE_URL,
        "source_sha256": source["archive_sha256"],
        "csv_member_sha256": source["csv_member_sha256"],
        "split_seed": 7171, "target": "alpha_i=train client n_i / sum n_j; alpha-standardized empirical assessment",
        "schema_policy": "training-only bounds/vocab; pdays categorical atom 999; decimal scale 1000",
        "adult_selection_table_sha256": selection["selection_table_sha256"],
        "adult_selected_generator": "copula", "runner_up": "chow_liu",
        "generators": list(FAMILIES), "partitions": list(PARTITIONS), "k": 5,
        "severity": .8, "master_seeds": list(SEEDS), "cells": cells,
        "local_grid": [{"bins": bins, "alpha": alpha} for bins in (8, 16, 32) for alpha in (.1, 1.)],
        "local_tune_samples": TUNE_SAMPLE,
        "local_tune_criterion": "local-tune primary-query MAE versus one model draw; finite score/support/convergence required",
        "pilot_rows_per_client": PILOT_PER_CLIENT,
        "methods": ["size", "uniform", "constrained_query_minimax"],
        "constraints": {"delta_l1": .25, "floor_ratio": .5},
        "synthetic_rows": N_SYNTH, "synthetic_repeats": REPEATS,
        "sample_allocation": "largest_remainder", "practical_gain_margin": .005,
        "substreams": {"local_fit": "master+100000*client+trial",
                       "local_tune_draw": "master+200000*client+1000+trial",
                       "pilot": "master+3000+client*1009",
                       "assessment_draw": "master+5200+rep"},
        "access": "nonprivate released models, train-derived schema/counts, aggregate calibration query vector, synthetic pilots; no real per-record scores to weighting server",
        "assessment_used_for_design_or_selection": False,
        "adult_method_reselection_from_external": False,
        "utility_policy": "C in .1/1/10 by source-specific tune Brier; separate source-specific Platt sigmoid; TSTR train10000/tune2000/cal2000; full privileged TRTR; clipped probabilities at 1e-6; alpha-weighted assessment",
        "source_file_sha256": scoring_sources(),
        "inputs": {str(p.relative_to(ROOT)): sha(p) for p in (
            DATA / "bank_marketing_uci.zip", DATA / "data_manifest.json",
            DATA / "schema.json", DATA / "split_manifest.csv", DATA / "cleaned.csv", query_path,
            ROOT / "reports/completion_selection_20261025/global_generator_validation_selection.csv")},
    }
    FREEZE.write_bytes(canonical(freeze))
    FREEZE.with_suffix(".json.sha256").write_text(sha(FREEZE) + "\n")
    write_json(DATA / "cell_manifest.json", {"cells": cells, "freeze_sha256": sha(FREEZE)})
    return freeze


def validate_freeze() -> dict:
    if not FREEZE.is_file():
        raise ValueError("External protocol freeze missing")
    freeze = json.loads(FREEZE.read_text())
    if FREEZE.read_bytes() != canonical(freeze):
        raise ValueError("External freeze serialization differs")
    if not FREEZE.with_suffix(".json.sha256").is_file() or FREEZE.with_suffix(".json.sha256").read_text().strip() != sha(FREEZE):
        raise ValueError("External freeze sidecar mismatch")
    if freeze.get("assessment_used_for_design_or_selection") is not False or freeze.get("adult_method_reselection_from_external") is not False:
        raise ValueError("External access gate invalid")
    if freeze.get("cells") != [{"generator": g, "partition": p, "k": 5, "seed": s}
                               for g in FAMILIES for p in PARTITIONS for s in SEEDS]:
        raise ValueError("External cell manifest changed")
    if freeze.get("source_file_sha256") != scoring_sources():
        raise ValueError("External scoring source changed since freeze")
    for rel, digest in freeze["inputs"].items():
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or sha(path) != digest:
            raise ValueError(f"External frozen input mismatch: {rel}")
    return freeze


def checked_capacity() -> dict:
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    mem = Path("/proc/meminfo").read_text()
    available = next(int(line.split()[1]) * 1024 for line in mem.splitlines() if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve would be breached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve would be breached")
    return resources


def client_parts(parts: dict, rule, k: int) -> tuple[dict, pd.DataFrame]:
    assignments = {}
    groups = {}
    for split, frame in parts.items():
        ids = rule.assign(frame)
        assignments[split] = ids
        groups[split] = [frame.iloc[np.flatnonzero(ids == i)].copy() for i in range(k)]
    manifest = pd.concat([pd.DataFrame({"row_id": frame.index, "split": split,
                                        "client": assignments[split]})
                          for split, frame in parts.items()], ignore_index=True)
    return groups, manifest.sort_values("row_id")


def fit_local(name: str, train: pd.DataFrame, tune: pd.DataFrame, primary,
              schema: dict, seed: int, client: int, grid: list[dict]) -> tuple[object, dict]:
    trials = []
    best = None
    for j, parameters in enumerate(grid):
        started = time.monotonic()
        try:
            settings = {**parameters,
                        "numeric_bounds": schema["numeric_bounds_training_only"],
                        "category_vocab": schema["category_vocab_training_only"]}
            model = fit_model(name, train, seed + 100000 * client + j, settings)
            sample = model.sample(TUNE_SAMPLE, seed + 200000 * client + 1000 + j)
            error = float(np.mean(np.abs(primary.mean(tune) - primary.mean(sample))))
            finite = float(np.isfinite(model.log_prob(tune.iloc[:min(64, len(tune))])).mean())
            valid = sample[LABEL].isin(["yes", "no"]).all()
            converged = bool(getattr(getattr(model, "gmm", None), "converged_", True))
            eligible = bool(np.isfinite(error) and finite == 1 and valid and converged)
            trial = {"parameters": parameters, "local_tune_query_mae": error,
                     "finite_tune_score_fraction": finite, "valid_outcome": bool(valid),
                     "converged": converged, "wall_seconds": time.monotonic() - started,
                     "status": "eligible" if eligible else "nonconverged_or_invalid",
                     "likelihood_kind": model.likelihood_kind}
            trials.append(trial)
            if eligible and (best is None or (error, j) < (best[0], best[1])):
                best = error, j, model, parameters
        except Exception as exc:
            trials.append({"parameters": parameters, "status": "failed",
                           "error": f"{type(exc).__name__}: {exc}",
                           "wall_seconds": time.monotonic() - started})
    if best is None:
        raise RuntimeError(f"No eligible {name} client model: {trials}")
    return best[2], {"selected": best[3], "trials": trials, "train_rows": len(train),
                     "tune_rows": len(tune), "used_split": "train/local tune only"}


def run_cell(spec: dict, freeze: dict) -> None:
    started = time.monotonic()
    name, kind, k, seed = (spec[x] for x in ("generator", "partition", "k", "seed"))
    cell = RESULTS / f"{name}_{kind}_k{k}_s{seed}"
    cell.mkdir(parents=True, exist_ok=True)
    config = {"spec": spec, "freeze_sha256": sha(FREEZE),
              "source_file_sha256": freeze["source_file_sha256"],
              "created_at_utc": utc(), "hostname": platform.node(),
              "python": sys.version, "pid": os.getpid()}
    existing = cell / "configuration.json"
    if existing.is_file():
        old = json.loads(existing.read_text())
        if old["spec"] != spec or old["freeze_sha256"] != config["freeze_sha256"]:
            raise ValueError("Incompatible cached external cell")
    else:
        write_json(existing, config)
    if (cell / "complete.json").is_file():
        return
    parts, _ = rebuild_allowed_parts()
    schema = json.loads((DATA / "schema.json").read_text())
    primary, audit = workloads(parts["train"], schema)
    if workload_hash(primary, audit) != sha(DATA / "workloads.json"):
        raise ValueError("External workload changed")
    rule = fit_partition_rule(parts["train"], kind, k, seed, freeze["severity"])
    groups, manifest = client_parts(parts, rule, k)
    manifest.to_csv(cell / "partition_manifest.csv", index=False)
    write_json(cell / "partition_rule.json", rule.__dict__)
    alpha_counts = np.asarray([len(frame) for frame in groups["train"]], int)
    if (alpha_counts <= 0).any() or any(len(frame) == 0 for split in groups.values() for frame in split):
        raise ValueError("Positive-mass client has no training/reference support")
    alpha = alpha_counts / alpha_counts.sum()
    write_json(cell / "target.json", {"counts": alpha_counts.tolist(), "alpha": alpha.tolist(),
               "reference_counts": {s: [len(f) for f in grp] for s, grp in groups.items()}})
    models = []
    for i in range(k):
        checkpoint = cell / f"client_{i}.pkl"
        tuning = cell / f"tuning_{i}.json"
        if checkpoint.is_file() and tuning.is_file():
            model = pickle.loads(checkpoint.read_bytes())
        else:
            model, trials = fit_local(name, groups["train"][i], groups["tune"][i],
                                      primary, schema, seed, i, freeze["local_grid"])
            write_json(tuning, trials)
            temp = checkpoint.with_suffix(".pkl.tmp")
            temp.write_bytes(pickle.dumps(model))
            temp.replace(checkpoint)
        models.append(model)
        if time.monotonic() - started > 3600:
            raise TimeoutError("Cell fitting ceiling exceeded")
    target_cal = weighted_reference(groups["calibration"], primary, alpha)
    H = np.column_stack([primary.mean(m.sample(PILOT_PER_CLIENT, seed + 3000 + i * 1009))
                         for i, m in enumerate(models)])
    np.savez_compressed(cell / "permitted_summary.npz", H=H, b_calibration=target_cal, alpha=alpha)
    constrained, cert = constrained_query_minimax(H, target_cal, alpha, .25, .5)
    target_val = weighted_reference(groups["validation"], primary, alpha)
    oracle, oracle_cert = constrained_query_minimax(H, target_val, alpha, 2., 0.)
    weights = {"size": alpha, "uniform": np.ones(k)/k,
               "constrained_query_minimax": constrained}
    write_json(cell / "weights.json", {"weights": {n: w.tolist() for n, w in weights.items()},
               "constrained_certificate": cert,
               "fixed_pilot_validation_oracle": {"weights": oracle.tolist(), **oracle_cert},
               "access": freeze["access"]})
    # This timestamp is written before the first assessment endpoint is evaluated.
    write_json(cell / "assessment_access.json", {"first_read_utc": utc(),
               "freeze_sha256": sha(FREEZE), "read_purpose": "registered external assessment only"})
    reference = weighted_reference(groups["assessment"], primary, alpha)
    audit_reference = weighted_reference(groups["assessment"], audit, alpha)
    pooled_reference = primary.mean(pd.concat(groups["assessment"]))
    pooled_audit_reference = audit.mean(pd.concat(groups["assessment"]))
    metrics, answers = [], []
    for method, w in weights.items():
        for rep in range(REPEATS):
            draw_seed = seed + 5200 + rep
            synth, counts = sample_mixture(models, w, N_SYNTH, draw_seed)
            if counts.sum() != N_SYNTH or not synth[LABEL].isin(["yes", "no"]).all():
                raise ValueError("Invalid synthetic draw")
            q = primary.mean(synth)
            a = audit.mean(synth)
            errors = np.abs(q - reference)
            audit_errors = np.abs(a - audit_reference)
            invalid_categories = sum((~synth[c].isin(schema["category_vocab_training_only"][c])).sum()
                                     for c in schema["category_vocab_training_only"])
            invalid_numeric = sum(((synth[c] < bounds[0]) | (synth[c] > bounds[1])).sum()
                                  for c, bounds in schema["numeric_bounds_training_only"].items())
            metrics.append({"generator": name, "partition": kind, "k": k, "seed": seed,
                            "method": method, "replicate": rep, "draw_seed": draw_seed,
                            "query_linf": float(errors.max()), "query_mae": float(errors.mean()),
                            "audit_query_linf": float(audit_errors.max()),
                            "audit_query_mae": float(audit_errors.mean()),
                            "pooled_reference_query_linf_secondary": float(np.abs(q - pooled_reference).max()),
                            "weight_l1_from_alpha": float(np.abs(w-alpha).sum()),
                            "minimum_weight_alpha_ratio": float(np.min(w/alpha)),
                            "unique_row_fraction": float(len(synth.drop_duplicates())/len(synth)),
                            "invalid_support_count": int(invalid_categories + invalid_numeric),
                            "n_synthetic": N_SYNTH, "n_real_reference": sum(map(len, groups["assessment"])),
                            "allocation_counts": json.dumps(counts.tolist())})
            for workload_name, queryset, real, pooled, synthetic in (
                ("primary", primary.queries, reference, pooled_reference, q),
                ("audit", audit.queries, audit_reference, pooled_audit_reference, a)):
                for query, real_value, pooled_value, synthetic_value in zip(queryset, real, pooled, synthetic):
                    answers.append({"method": method, "replicate": rep, "workload": workload_name,
                                    "query": query.name, "real_alpha": float(real_value),
                                    "real_pooled_secondary": float(pooled_value),
                                    "synthetic": float(synthetic_value),
                                    "absolute_error": float(abs(real_value - synthetic_value))})
    pd.DataFrame(metrics).to_csv(cell / "metrics.csv", index=False)
    pd.DataFrame(answers).to_csv(cell / "query_answers.csv", index=False)
    evaluate_utility(cell, groups, models, weights, alpha, seed)
    write_json(cell / "complete.json", {"status": "complete", "finished_at_utc": utc(),
               "elapsed_seconds": time.monotonic() - started,
               "metrics_sha256": sha(cell / "metrics.csv"),
               "query_answers_sha256": sha(cell / "query_answers.csv"),
               "utility_metrics_sha256": sha(cell / "utility_metrics.csv"),
               "utility_predictions_sha256": sha(cell / "utility_predictions.csv")})


def run_batch() -> None:
    freeze = validate_freeze()
    vendor = (Path("/sys/devices/virtual/dmi/id/sys_vendor").read_text(errors="ignore") +
              Path("/sys/devices/virtual/dmi/id/product_name").read_text(errors="ignore"))
    if "amazon" not in vendor.lower() and "ec2" not in vendor.lower():
        raise RuntimeError("External fitting must run on the verified existing EC2")
    resources = checked_capacity()
    lease = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lease.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    RESULTS.mkdir(parents=True, exist_ok=True)
    with lease.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for spec in freeze["cells"]:
            if time.monotonic() - started >= resources["campaign_wall_seconds"]:
                break
            checked_capacity()
            name = f'{spec["generator"]}_{spec["partition"]}_k5_s{spec["seed"]}'
            cell = RESULTS / name
            if (cell / "complete.json").is_file():
                continue
            log = ROOT / "logs" / f"external_bank_{name}.log"
            env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                   "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1", "BTP_LEASE_HELD": "1"}
            command = [sys.executable, __file__, "--cell", name]
            before = time.monotonic()
            with log.open("a") as stream:
                stream.write(f"{utc()} COMMAND {command}\n")
                try:
                    result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                            timeout=min(resources["cell_timeout_seconds"],
                                                        max(1, resources["campaign_wall_seconds"] - (time.monotonic()-started))))
                    status = "complete" if result.returncode == 0 else "failed"
                except subprocess.TimeoutExpired:
                    status = "timed_out_checkpoint_retained"
            write_json(cell / "scheduler_status.json", {"status": status,
                       "wall_seconds": time.monotonic()-before, "log": str(log.relative_to(ROOT)),
                       "at_utc": utc()})
            print(name, status, flush=True)
            if status != "complete":
                break


def report() -> None:
    freeze = validate_freeze()
    rows, failures = [], []
    for spec in freeze["cells"]:
        cell = RESULTS / f'{spec["generator"]}_{spec["partition"]}_k5_s{spec["seed"]}'
        if (cell / "complete.json").is_file():
            metrics = pd.read_csv(cell / "metrics.csv")
            if len(metrics) != 3*REPEATS:
                raise ValueError(f"Incomplete metric rows: {cell}")
            rows.extend(metrics.to_dict("records"))
        else:
            status = json.loads((cell / "scheduler_status.json").read_text()) if (cell / "scheduler_status.json").is_file() else {"status": "not_started"}
            failures.append({**spec, **status})
    REPORTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(REPORTS / "all_draws.csv", index=False)
    pd.DataFrame(failures).to_csv(REPORTS / "failed_or_missing_cells.csv", index=False)
    if rows:
        frame = pd.DataFrame(rows)
        cell = frame.groupby(["generator", "partition", "seed", "method"], as_index=False).agg(
            query_linf_mean=("query_linf", "mean"), query_mae_mean=("query_mae", "mean"),
            audit_query_linf_mean=("audit_query_linf", "mean"),
            weight_l1=("weight_l1_from_alpha", "first"),
            invalid_support_count=("invalid_support_count", "sum"))
        cell.to_csv(REPORTS / "cell_means.csv", index=False)
        pivot = cell.pivot(index=["generator", "partition", "seed"], columns="method", values="query_linf_mean")
        pivot["constrained_minus_size"] = pivot["constrained_query_minimax"] - pivot["size"]
        pivot.to_csv(REPORTS / "paired_differences.csv")
    print(json.dumps({"complete_cells": len(rows)//(3*REPEATS), "failed_or_missing": len(failures),
                      "report_root": str(REPORTS.relative_to(ROOT))}))


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-freeze", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--cell")
    mode.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.prepare_freeze:
        result = prepare_freeze()
        print(json.dumps({"freeze_sha256": sha(FREEZE), "cells": len(result["cells"])}))
    elif args.run:
        run_batch()
    elif args.report:
        report()
    elif args.cell:
        if os.environ.get("BTP_LEASE_HELD") != "1":
            raise RuntimeError("Cell may only run inside the shared-lease scheduler")
        freeze = validate_freeze()
        names = {f'{c["generator"]}_{c["partition"]}_k5_s{c["seed"]}': c for c in freeze["cells"]}
        if args.cell not in names:
            raise ValueError("Unregistered external cell")
        try:
            run_cell(names[args.cell], freeze)
        except Exception:
            cell = RESULTS / args.cell
            cell.mkdir(parents=True, exist_ok=True)
            write_json(cell / "failure.json", {"status": "failed", "at_utc": utc(),
                       "traceback": traceback.format_exc(), "freeze_sha256": sha(FREEZE)})
            raise


if __name__ == "__main__":
    main()
