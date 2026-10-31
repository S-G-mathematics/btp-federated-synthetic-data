"""Finite-query empirical conditional transfer on fixed projected teachers."""
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
from btp.evaluation import CONDITIONS, Workload, sample_mixture
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash, conditional_reference
from representation_constrained import reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
CONSTRAINED = ROOT / "results/representation_constrained_projected_v2_deterministic_20261024"
CONDITIONAL = ROOT / "results/projected_conditionals_v2_20261024"
OUTPUT = ROOT / "results/projected_transfer_20261025"
TEACHER_ROWS = 30000
MIN_TEACHER_ROWS, MIN_TEACHER_MASS = 300, .01


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared RAM reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def ratio_bound(joint_error: float, mass_error: float, real_mass: float) -> float:
    if real_mass <= 0:
        raise ValueError("Real condition mass must be positive")
    return min(1., (joint_error + mass_error) / real_mass)


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Incompatible projected development cell")
    prior_cell = CONDITIONAL / cell.name
    prior_cfg = json.loads((prior_cell / "configuration.json").read_text())
    if prior_cfg["source_code_hash"] != cfg["code_hash"]:
        raise ValueError("Incompatible prior conditional cell")
    prior = pd.read_csv(prior_cell / "condition_metrics.csv")
    prior_answers = pd.read_csv(prior_cell / "condition_query_answers.csv")
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    fitted = json.loads((CONSTRAINED / cell.name / "weight_fits.json").read_text())
    vectors = {m: np.asarray(fitted[m]["weights"], float) for m in ("size", "constrained")}
    if not np.allclose(vectors["size"], alpha):
        raise ValueError("Size weights differ from alpha")
    models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
              for i in range(cfg["k"])]
    primary, _ = projected_workloads_v2(public_schema())
    feature = Workload([q for q in primary.queries if all(t[0] != "income" for t in q.terms)])
    parts = reference_parts(cell, cfg, alpha)["test"]
    rows, query_rows, triangle_rows = [], [], []
    for method, vector in vectors.items():
        capacity(resources)
        if time.monotonic() - started >= resources["cell_timeout_seconds"]:
            raise TimeoutError("Transfer cell wall limit reached")
        seed = cfg["seed"] + 71000
        teacher, counts = sample_mixture(models, vector, TEACHER_ROWS, seed)
        if len(teacher) != TEACHER_ROWS or counts.sum() != TEACHER_ROWS:
            raise ValueError("Teacher count mismatch")
        teacher_q = feature.transform(teacher)
        for condition in CONDITIONS:
            real_cond, real_mass, real_count = conditional_reference(parts, alpha, condition, feature)
            mask = np.asarray(condition.evaluate(teacher), bool)
            syn_count, syn_mass = int(mask.sum()), float(mask.mean())
            previous = prior.loc[(prior.method == method) & (prior.condition == condition.name)]
            supported = (syn_count >= MIN_TEACHER_ROWS and syn_mass >= MIN_TEACHER_MASS)
            if (len(previous) != (2 if supported else 1) or previous.teacher_matching_rows.nunique() != 1
                or int(previous.teacher_matching_rows.iloc[0]) != syn_count
                or not np.isclose(previous.teacher_condition_mass.iloc[0], syn_mass, atol=1e-12)
                or not np.isclose(previous.real_alpha_condition_mass.iloc[0], real_mass, atol=1e-12)):
                raise ValueError(f"Prior teacher/reference mismatch: {method}/{condition.name}")
            if supported != (set(previous.status) == {"completed"}):
                raise ValueError(f"Support gate mismatch: {method}/{condition.name}")
            base = {"method": method, "condition": condition.name,
                    "real_alpha_mass": real_mass, "real_count_pooled": real_count,
                    "synthetic_teacher_mass": syn_mass, "synthetic_teacher_count": syn_count,
                    "teacher_seed": seed, "support_status": "supported" if supported else "abstain"}
            if real_cond is None or syn_count == 0:
                rows.append({**base, "status": "undefined_conditional"})
                continue
            real_joint = real_cond * real_mass
            syn_joint = (teacher_q * mask[:, None]).mean(axis=0)
            syn_cond = teacher_q[mask].mean(axis=0)
            joint_errors = np.abs(syn_joint - real_joint)
            mass_error = abs(syn_mass - real_mass)
            actual = np.abs(syn_cond - real_cond)
            bound = ratio_bound(float(joint_errors.max()), mass_error, real_mass)
            if float(actual.max()) > bound + 1e-10:
                raise AssertionError("Finite-query ratio inequality failed")
            rows.append({**base, "status": "computed", "joint_query_linf": float(joint_errors.max()),
                         "condition_mass_error": mass_error,
                         "observed_conditional_linf": float(actual.max()),
                         "empirical_ratio_bound": bound,
                         "bound_minus_observed": bound - float(actual.max())})
            for q, r, s, j, err in zip(feature.queries, real_cond, syn_cond, joint_errors, actual):
                query_rows.append({**base, "query": q.name, "real_conditional_answer": float(r),
                                   "synthetic_teacher_conditional_answer": float(s),
                                   "absolute_joint_intersection_error": float(j),
                                   "absolute_conditional_error": float(err)})
            if not supported:
                continue
            saved = prior_answers.loc[(prior_answers.method == method) &
                                      (prior_answers.condition == condition.name)]
            pivot = saved.pivot(index="query", columns="route", values="synthetic_answer")
            for q in feature.queries:
                direct = float(pivot.loc[q.name, "direct_teacher_rejection"])
                student = float(pivot.loc[q.name, "trained_student_postfilter"])
                reference = float(real_cond[[x.name for x in feature.queries].index(q.name)])
                direct_error, student_error = abs(direct-reference), abs(student-reference)
                discrepancy = abs(student-direct)
                if student_error > direct_error + discrepancy + 1e-10:
                    raise AssertionError("Student/direct empirical triangle failed")
                triangle_rows.append({"method": method, "condition": condition.name,
                    "query": q.name, "real_conditional_answer": reference,
                    "direct_teacher_answer": direct, "student_postfilter_answer": student,
                    "direct_real_error": direct_error, "student_real_error": student_error,
                    "student_direct_discrepancy": discrepancy,
                    "triangle_upper_bound": direct_error + discrepancy})
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "condition_bounds.csv", index=False)
    pd.DataFrame(query_rows).to_csv(out / "teacher_query_answers.csv", index=False)
    pd.DataFrame(triangle_rows).to_csv(out / "student_teacher_triangles.csv", index=False)
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)), "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "source_workloads_sha256": hashlib.sha256((cell / "workloads.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prior_conditional_config_sha256": hashlib.sha256((prior_cell / "configuration.json").read_bytes()).hexdigest(),
        "teacher_rows": TEACHER_ROWS, "teacher_seed_offset": 71000,
        "methods": list(vectors), "reference_role": cfg["reference_role"],
        "official_test_used": False, "elapsed_seconds": time.monotonic()-started,
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
    targets = [(g, p, k, seed) for g, p, k in
               (("chow_liu", "age", 5), ("mixed_gmm", "label_skew", 10))
               for seed in (101, 202, 303)]
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        began, completed = time.monotonic(), 0
        for g, p, k, seed in targets:
            if completed >= args.max_cells or time.monotonic()-began >= resources["campaign_wall_seconds"]:
                break
            matches = list(SOURCE.glob(f"{g}_{p}_k{k}_s{seed}_*"))
            if len(matches) != 1:
                raise ValueError("Expected one source cell")
            cell, = matches
            out = OUTPUT / cell.name
            marker = out / "configuration.json"
            if marker.exists():
                saved = json.loads(marker.read_text())
                if (saved.get("status") == "complete" and saved.get("source_code_hash") == code_hash()
                    and saved.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible existing transfer cell: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior transfer failure retained: {out}")
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
