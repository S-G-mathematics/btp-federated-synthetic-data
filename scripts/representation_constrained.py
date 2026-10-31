"""Fixed-target query calibration from released summaries and models.

The solver sees only permitted H, b and alpha. Real validation/assessment rows
enter this privileged evaluator only after weights are fixed. This is a
development comparison, not a private mechanism or a global selection rule.
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
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, prepare_splits
from btp.evaluation import empirical_metrics, public_workloads, sample_mixture, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2

DELTA = 0.25
FLOOR_RATIO = 0.5
ROWS = 10000
REPEATS = 5


def constrained_query_minimax(
    H: np.ndarray, b: np.ndarray, alpha: np.ndarray,
    delta: float, floor_ratio: float,
) -> tuple[np.ndarray, dict]:
    H = np.asarray(H, float)
    b = np.asarray(b, float)
    alpha = np.asarray(alpha, float)
    L, K = H.shape
    if (
        b.shape != (L,) or alpha.shape != (K,)
        or not np.isfinite(H).all() or not np.isfinite(b).all()
        or not np.isfinite(alpha).all() or not np.isclose(alpha.sum(), 1)
        or np.min(alpha) <= 0 or not 0 <= delta <= 2
        or not 0 <= floor_ratio <= 1
    ):
        raise ValueError("Invalid permitted summaries or constraints")
    # Variables are (w_1..w_K, u_1..u_K, t), with u >= |w-alpha|.
    objective = np.zeros(2 * K + 1)
    objective[-1] = 1.0
    identity = np.eye(K)
    zeros = np.zeros((L, K))
    trailing = np.zeros((K, 1))
    Aub = np.vstack([
        np.c_[H, zeros, -np.ones((L, 1))],
        np.c_[-H, zeros, -np.ones((L, 1))],
        np.c_[identity, -identity, trailing],
        np.c_[-identity, -identity, trailing],
        np.r_[np.zeros(K), np.ones(K), 0.0][None, :],
    ])
    bub = np.r_[b, -b, alpha, -alpha, delta]
    equality = np.r_[np.ones(K), np.zeros(K + 1)][None, :]
    bounds = (
        [(float(floor_ratio * a), 1.0) for a in alpha]
        + [(0.0, None)] * K + [(0.0, None)]
    )
    result = linprog(
        objective, A_ub=Aub, b_ub=bub, A_eq=equality, b_eq=[1.0],
        bounds=bounds, method="highs",
    )
    if not result.success:
        raise RuntimeError(f"HiGHS failed: {result.message}")
    weights = result.x[:K]
    actual_l1 = float(np.abs(weights - alpha).sum())
    if (
        not np.isclose(weights.sum(), 1.0, atol=1e-7)
        or np.min(weights - floor_ratio * alpha) < -1e-7
        or actual_l1 > delta + 1e-7
    ):
        raise RuntimeError("HiGHS returned infeasible weights")
    return weights, {
        "solver": "HiGHS",
        "success": True,
        "status": int(result.status),
        "message": result.message,
        "objective_calibration_query_linf": float(np.max(np.abs(H @ weights - b))),
        "actual_weight_l1": actual_l1,
        "minimum_weight_alpha_ratio": float(np.min(weights / alpha)),
        "effective_client_count": float(1.0 / np.sum(weights**2)),
        "delta": delta,
        "floor_ratio": floor_ratio,
    }


def self_test() -> None:
    H = np.eye(2)
    b = np.array([0.9, 0.1])
    alpha = np.array([0.5, 0.5])
    size, _ = constrained_query_minimax(H, b, alpha, 0.0, 1.0)
    limited, cert = constrained_query_minimax(H, b, alpha, 0.25, 0.5)
    full, _ = constrained_query_minimax(H, b, alpha, 2.0, 0.0)
    np.testing.assert_allclose(size, alpha, atol=1e-8)
    np.testing.assert_allclose(limited, [0.625, 0.375], atol=1e-8)
    np.testing.assert_allclose(full, b, atol=1e-8)
    assert cert["actual_weight_l1"] <= 0.25 + 1e-8
    assert cert["minimum_weight_alpha_ratio"] >= 0.5 - 1e-8


def reference_parts(cell: Path, cfg: dict, alpha: np.ndarray) -> dict:
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat(
        [splits[name] for name in ("train", "tune", "calibration", "validation")]
    )
    if not manifest.row_id.isin(development.index).all():
        raise ValueError(f"Manifest row ID mismatch: {cell}")
    joined = manifest.join(development, on="row_id", validate="one_to_one")
    parts = {
        split: [
            joined[(joined.split == split) & (joined.client == i)][
                list(ALL_COLUMNS)
            ].copy()
            for i in range(cfg["k"])
        ]
        for split in ("validation", "test")
    }
    if any(len(part) < 2 for groups in parts.values() for part in groups):
        raise ValueError(f"Insufficient client reference support: {cell}")
    return parts


def check_capacity(resources: dict) -> None:
    meminfo = Path("/proc/meminfo").read_text()
    available = next(
        int(line.split()[1]) * 1024 for line in meminfo.splitlines()
        if line.startswith("MemAvailable:")
    )
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Available RAM below shared reserve")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Free disk below shared reserve")


def run_cell(cell: Path, output: Path) -> None:
    cfg = json.loads((cell / "configuration.json").read_text())
    if cfg["reference_role"] != "development_assessment":
        raise ValueError("Official test is outside this script")
    output.mkdir(parents=True, exist_ok=True)
    summary = np.load(cell / "releases/permitted_summary.npz")
    H, b, alpha = (
        summary["H"], summary["target_query_mean"], summary["alpha"]
    )
    models = [
        pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
        for i in range(cfg["k"])
    ]
    parts = reference_parts(cell, cfg, alpha)
    version = cfg.get("workload_version", "historical_v1")
    if version == "projected_v2":
        workload, audit = projected_workloads_v2(public_schema())
    elif version == "historical_v1":
        workload, audit = public_workloads(public_schema())
    else:
        raise ValueError(f"Unsupported workload version: {version}")
    declared_workloads = json.loads((cell / "workloads.json").read_text())
    expected_workloads = json.loads(json.dumps({
        "calibration": workload.to_dict(), "unseen_audit": audit.to_dict()
    }))
    if declared_workloads != expected_workloads:
        raise ValueError("Source workload differs from selected version; do not mix pilots and endpoints")
    weights = {"size": alpha}
    certificates = {
        "size": {
            "success": True, "delta": 0.0, "floor_ratio": 1.0,
            "actual_weight_l1": 0.0,
        }
    }
    for name, delta, floor in (
        ("constrained", DELTA, FLOOR_RATIO),
        ("unconstrained", 2.0, 0.0),
    ):
        weights[name], certificates[name] = constrained_query_minimax(
            H, b, alpha, delta, floor
        )
    q_alpha = weighted_reference(parts["test"], workload, alpha)
    pooled = pd.concat(parts["test"])
    q_pooled = workload.mean(pooled)
    target_gap = float(np.max(np.abs(q_alpha - q_pooled)))
    records = []
    for name, w in weights.items():
        for split in ("validation", "test"):
            repetitions = [0] if split == "validation" else range(REPEATS)
            for rep in repetitions:
                seed = cfg["seed"] + (4200 if split == "validation" else 5200) + rep
                synthetic, counts = sample_mixture(models, w, ROWS, seed)
                if counts.sum() != ROWS:
                    raise RuntimeError("Synthetic allocation not exact")
                metrics = empirical_metrics(
                    parts[split], synthetic, workload, audit, alpha
                )
                pooled_loss = float(
                    np.max(np.abs(workload.mean(synthetic) - workload.mean(
                        pd.concat(parts[split])
                    )))
                )
                records.append({
                    "method": name,
                    "split": (
                        "development_validation" if split == "validation"
                        else "development_assessment"
                    ),
                    "replicate": rep,
                    "seed": seed,
                    "pooled_reference_query_linf_secondary": pooled_loss,
                    "weight_l1_from_alpha": float(np.abs(w - alpha).sum()),
                    "minimum_weight_alpha_ratio": float(np.min(w / alpha)),
                    "effective_client_count": float(1.0 / np.sum(w**2)),
                    **metrics,
                })
    result = pd.DataFrame(records)
    result.to_csv(output / "metrics.csv", index=False)
    (output / "weight_fits.json").write_text(
        json.dumps({
            name: {"weights": w.tolist(), **certificates[name]}
            for name, w in weights.items()
        }, indent=2) + "\n"
    )
    (output / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "workload_version": version,
        "source_workloads_sha256": hashlib.sha256(
            (cell / "workloads.json").read_bytes()
        ).hexdigest(),
        "source_manifest_sha256": hashlib.sha256(
            (cell / "partition_manifest.csv").read_bytes()
        ).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "delta": DELTA, "floor_ratio": FLOOR_RATIO,
        "rows": ROWS, "assessment_repeats": REPEATS,
        "primary_reference": "alpha-standardized client held-out query means",
        "pooled_reference": "secondary unweighted pooled held-out query means",
        "assessment_target_gap_query_linf": target_gap,
        "official_test_used": False,
        "status": "complete",
        "ended_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(cell.name, "complete", flush=True)


def main() -> None:
    self_test()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports/core_matrix_audit_20261024/manifest.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results/representation_constrained_20261024")
    parser.add_argument("--max-cells", type=int, default=6)
    parser.add_argument("--wall-seconds", type=int, default=7200)
    args = parser.parse_args()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lease_path = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        started = time.monotonic()
        manifest = pd.read_csv(args.manifest)
        if "cell" not in manifest:
            raise ValueError("Manifest must name source cell paths")
        eligible = (manifest[
            manifest.status.isin(("complete_exact", "reuse_with_selection_bridge"))
        ] if "status" in manifest else manifest)
        completed = 0
        for row in eligible.itertuples():
            if completed >= args.max_cells:
                break
            if time.monotonic() - started >= min(
                args.wall_seconds, resources["campaign_wall_seconds"]
            ):
                break
            cell = ROOT / row.cell
            output = args.out / cell.name
            marker = output / "configuration.json"
            failure = output / "failure.json"
            if marker.exists():
                prior = json.loads(marker.read_text())
                if (
                    prior.get("status") == "complete"
                    and prior.get("source_manifest_sha256")
                    == hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest()
                    and prior.get("script_sha256")
                    == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                ):
                    continue
                raise RuntimeError(f"Incompatible existing output: {output}")
            if failure.exists():
                raise RuntimeError(f"Previous failed attempt retained: {failure}")
            check_capacity(resources)
            try:
                run_cell(cell, output)
            except Exception as exc:
                output.mkdir(parents=True, exist_ok=True)
                failure.write_text(json.dumps({
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
