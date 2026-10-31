"""Registered-condition teacher rejection versus trained non-neural student."""
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
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from btp.data import PREDICTORS
from btp.evaluation import CONDITIONS, Workload, sample_mixture
from btp.models import fit_model
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.projection import EducationNumberProjection
from btp.run import code_hash, conditional_reference
from representation_constrained import reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
OUTPUT = ROOT / "results/projected_conditionals_v2_20261024"
TEACHER_ROWS = 30000
REQUESTED_ROWS = 2000
MIN_TEACHER_ROWS = 300
MIN_TEACHER_MASS = .01


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Incompatible projected development cell")
    constrained = CONSTRAINED / cell.name
    fitted = json.loads((constrained / "weight_fits.json").read_text())
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    weights = {method: np.asarray(fitted[method]["weights"], float)
               for method in ("size", "constrained")}
    if not np.allclose(weights["size"], alpha):
        raise ValueError("Fixed size weights differ from target")
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    schema = public_schema()
    workload, _ = projected_workloads_v2(schema)
    feature_workload = Workload([query for query in workload.queries
                                if all(term[0] != "income" for term in query.terms)])
    parts = reference_parts(cell, cfg, alpha)["test"]
    out.mkdir(parents=True, exist_ok=True)
    records, query_rows, settings_rows = [], [], []
    for method, vector in weights.items():
        capacity(resources)
        teacher_seed = cfg["seed"] + 71000
        teacher, counts = sample_mixture(models, vector, TEACHER_ROWS, teacher_seed)
        if len(teacher) != TEACHER_ROWS or counts.sum() != TEACHER_ROWS:
            raise RuntimeError("Teacher mixture allocation mismatch")
        direct_seed = cfg["seed"] + 74000
        direct_pool, direct_counts = sample_mixture(models, vector, TEACHER_ROWS, direct_seed)
        if len(direct_pool) != TEACHER_ROWS or direct_counts.sum() != TEACHER_ROWS:
            raise RuntimeError("Independent direct teacher allocation mismatch")
        settings_rows.append({"method": method, "teacher_seed": teacher_seed,
                              "teacher_client_counts": counts.tolist(),
                              "direct_seed": direct_seed,
                              "direct_client_counts": direct_counts.tolist(),
                              "weight_l1_from_alpha": float(np.abs(vector-alpha).sum())})
        for condition_index, condition in enumerate(CONDITIONS):
            if time.monotonic()-started >= resources["cell_timeout_seconds"]:
                raise TimeoutError("Conditional cell wall-time limit reached")
            mask = np.asarray(condition.evaluate(teacher), bool)
            subset = teacher.loc[mask, list(PREDICTORS)].copy()
            direct_subset = direct_pool.loc[np.asarray(condition.evaluate(direct_pool), bool),
                                            list(PREDICTORS)].copy()
            teacher_mass = len(subset) / TEACHER_ROWS
            real_reference, real_mass, real_count = conditional_reference(
                parts, alpha, condition, feature_workload)
            base = {"method": method, "condition": condition.name,
                    "teacher_pool_rows": TEACHER_ROWS,
                    "teacher_matching_rows": len(subset), "teacher_condition_mass": teacher_mass,
                    "real_alpha_condition_mass": real_mass, "real_assessment_condition_count": real_count,
                    "independent_direct_pool_rows": TEACHER_ROWS,
                    "independent_direct_matching_rows": len(direct_subset),
                    "support_threshold_rows": MIN_TEACHER_ROWS,
                    "support_threshold_mass": MIN_TEACHER_MASS,
                    "teacher_rows_drawn_per_matching_row": (TEACHER_ROWS/len(subset) if len(subset) else None)}
            if len(subset) < MIN_TEACHER_ROWS or teacher_mass < MIN_TEACHER_MASS:
                records.append({**base, "status": "abstain_insufficient_teacher_support"})
                continue
            train_seed = cfg["seed"] + 72000 + condition_index
            student_raw = fit_model("chow_liu", subset, train_seed, {
                "bins": 8, "alpha": .1,
                "numeric_bounds": schema["numeric_ranges"],
                "category_vocab": schema["categories"],
            })
            student = EducationNumberProjection(
                student_raw, schema["education_number_map"],
                tuple(schema["numeric_ranges"]["education-num"]))
            sample_seed = cfg["seed"] + 73000 + condition_index
            raw = student.sample(REQUESTED_ROWS, sample_seed)
            accepted = raw.loc[np.asarray(condition.evaluate(raw), bool)].copy()
            raw_accepted_rows = len(accepted)
            model_dir = out / "synthetic_conditional_models"
            model_dir.mkdir(parents=True, exist_ok=True)
            with (model_dir / f"{method}_{condition.name}.pkl").open("wb") as handle:
                pickle.dump(student, handle)
            if not len(accepted):
                records.append({**base, "status": "abstain_no_student_accepted_rows",
                                "student_raw_rows": REQUESTED_ROWS, "student_accepted_rows": 0,
                                "student_raw_violation": 1.0})
                continue
            if not len(direct_subset):
                records.append({**base, "status": "abstain_no_independent_direct_rows",
                                "student_raw_rows": REQUESTED_ROWS,
                                "student_accepted_rows": len(accepted),
                                "student_raw_violation": 1-len(accepted)/REQUESTED_ROWS})
                continue
            matched_rows = min(len(accepted), len(direct_subset))
            accepted = accepted.sample(n=matched_rows, random_state=sample_seed).reset_index(drop=True)
            direct = direct_subset.sample(n=matched_rows,
                                          random_state=sample_seed).reset_index(drop=True)
            accepted.to_csv(out / f"accepted_{method}_{condition.name}.csv.gz", index=False,
                            compression={"method": "gzip", "mtime": 0})
            for route, frame in (("direct_teacher_rejection", direct),
                                 ("trained_student_postfilter", accepted)):
                answers = feature_workload.mean(frame)
                for query, answer, truth in zip(feature_workload.queries, answers,
                                                real_reference if real_reference is not None else [np.nan]*len(answers)):
                    query_rows.append({"method": method, "condition": condition.name,
                                       "route": route, "query": query.name,
                                       "synthetic_answer": float(answer),
                                       "real_alpha_answer": float(truth),
                                       "abs_error": float(abs(answer-truth))})
                error = (np.abs(answers-real_reference)
                         if real_reference is not None else None)
                records.append({**base, "route": route,
                    "status": "completed" if error is not None else "assessment_reference_unavailable",
                    "generated_rows_evaluated": len(frame),
                    "matched_route_rows": matched_rows,
                    "student_raw_rows": REQUESTED_ROWS,
                    "student_accepted_rows": raw_accepted_rows,
                    "student_raw_violation": 1-raw_accepted_rows/REQUESTED_ROWS,
                    "student_postfilter_violation": 0.0,
                    "direct_teacher_accepted_rows_available": len(direct_subset),
                    "conditional_query_linf": float(error.max()) if error is not None else None,
                    "conditional_query_mae": float(error.mean()) if error is not None else None})
            settings_rows.append({"method": method, "condition": condition.name,
                                  "student_train_seed": train_seed,
                                  "student_sample_seed": sample_seed,
                                  "student_training_rows": len(subset),
                                  "estimator": "per-registered-condition projected Chow-Liu, no cross-condition generalization"})
    pd.DataFrame(records).to_csv(out / "condition_metrics.csv", index=False)
    pd.DataFrame(query_rows).to_csv(out / "condition_query_answers.csv", index=False)
    (out / "settings.json").write_text(json.dumps(settings_rows, indent=2) + "\n")
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "methods": list(weights), "condition_names": [q.name for q in CONDITIONS],
        "teacher_rows": TEACHER_ROWS, "requested_student_rows": REQUESTED_ROWS,
        "minimum_teacher_rows": MIN_TEACHER_ROWS,
        "minimum_teacher_mass": MIN_TEACHER_MASS,
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
                raise RuntimeError(f"Incompatible conditional output: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior failure retained: {out}")
            try:
                capacity(resources)
                run_cell(cell, out, resources)
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
