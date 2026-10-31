"""Matched zero-atom private/nonprivate histogram development comparison."""
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from btp.data import ALL_COLUMNS, prepare_splits
from btp.evaluation import empirical_metrics, sample_mixture
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash
from public_atom_histogram import declared_schema, fit_histogram
from representation_constrained import reference_parts

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
OUTPUT = ROOT / "results/public_atom_privacy_20261024"
EPSILONS = (1., 4., 8.)
ROWS, REPEATS = 10000, 5


def capacity(resources: dict) -> None:
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < resources["minimum_available_ram_gib"] * 2**30:
        raise RuntimeError("Shared memory reserve reached")
    if shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"] * 2**30:
        raise RuntimeError("Shared disk reserve reached")


def client_train_parts(cell: Path, cfg: dict) -> list[pd.DataFrame]:
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat([splits[name] for name in ("train", "tune", "calibration", "validation")])
    joined = manifest.join(development, on="row_id", validate="one_to_one")
    parts = [joined.loc[(joined.split == "train") & (joined.client == i),
                        list(ALL_COLUMNS)].copy() for i in range(cfg["k"])]
    if any(len(part) < 2 for part in parts):
        raise ValueError("Missing train client in fixed manifest")
    return parts


def rate(parts: list[pd.DataFrame], alpha: np.ndarray, column: str) -> float:
    return float(sum(a * frame[column].eq(0).mean() for a, frame in zip(alpha, parts)))


def mapping_violation(frame: pd.DataFrame, mapping: dict) -> float:
    expected = frame.education.map(mapping)
    known = expected.notna()
    if not known.any():
        return 0.
    return float((frame.loc[known, "education-num"] != expected.loc[known]).mean())


def run_cell(cell: Path, out: Path, resources: dict) -> None:
    started = time.monotonic()
    cfg = json.loads((cell / "configuration.json").read_text())
    if (cfg["reference_role"] != "development_assessment"
        or cfg["workload_version"] != "projected_v2" or cfg["code_hash"] != code_hash()):
        raise ValueError("Source cell is not compatible projected development")
    alpha = np.asarray(json.loads((cell / "partition.json").read_text())["alpha"], float)
    train = client_train_parts(cell, cfg)
    if not np.allclose(alpha, np.array([len(part) for part in train]) / sum(map(len, train))):
        raise ValueError("Fixed alpha differs from train mass")
    reference = reference_parts(cell, cfg, alpha)["test"]
    workload, audit = projected_workloads_v2(public_schema())
    schema_map = public_schema()["education_number_map"]
    real_gain_zero = rate(reference, alpha, "capital-gain")
    real_loss_zero = rate(reference, alpha, "capital-loss")
    rows, attacks, ledgers = [], [], []
    out.mkdir(parents=True, exist_ok=True)
    release_dir = out / "histogram_releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    for method, epsilon in (("nonprivate", None), ("epsilon_1", 1.),
                            ("epsilon_4", 4.), ("epsilon_8", 8.)):
        if time.monotonic()-started >= resources["cell_timeout_seconds"]:
            raise TimeoutError("Privacy cell wall-time limit reached")
        capacity(resources)
        began_fit = time.monotonic()
        models = [fit_histogram(frame, declared_schema(len(frame), bins=8), epsilon)
                  for frame in train]
        fit_seconds = time.monotonic()-began_fit
        for i, model in enumerate(models):
            ledgers.append({"method": method, "client": i, **model.privacy_ledger})
            n = min(300, len(train[i]), len(reference[i]))
            members = train[i].sample(n, random_state=cfg["seed"])
            nonmembers = reference[i].sample(n, random_state=cfg["seed"])
            scores = np.r_[model.log_prob(members), model.log_prob(nonmembers)]
            attacks.append({"method": method, "client": i, "member_count": n,
                            "nonmember_count": n,
                            "likelihood_membership_auc": float(roc_auc_score(
                                np.r_[np.ones(n), np.zeros(n)], scores)),
                            "finite_score_fraction": float(np.isfinite(scores).mean()),
                            "diagnostic_only_not_dp_proof": True})
        payload = pickle.dumps(models)
        (release_dir / f"{method}.pkl").write_bytes(payload)
        for rep in range(REPEATS):
            seed = cfg["seed"] + 81000 + rep
            began_draw = time.monotonic()
            synthetic, counts = sample_mixture(models, alpha, ROWS, seed)
            if len(synthetic) != ROWS or counts.sum() != ROWS:
                raise RuntimeError("Histogram mixture allocation mismatch")
            metrics = empirical_metrics(reference, synthetic, workload, audit, alpha)
            rows.append({"method": method, "epsilon_single_release": epsilon,
                         "replicate": rep, "synthetic_seed": seed,
                         "client_counts": json.dumps(counts.tolist()),
                         "model_bytes": len(payload), "fit_seconds": fit_seconds,
                         "draw_evaluate_seconds": time.monotonic()-began_draw,
                         "real_alpha_gain_zero": real_gain_zero,
                         "real_alpha_loss_zero": real_loss_zero,
                         "synthetic_gain_zero": float(synthetic["capital-gain"].eq(0).mean()),
                         "synthetic_loss_zero": float(synthetic["capital-loss"].eq(0).mean()),
                         "mapped_education_violation": mapping_violation(synthetic, schema_map),
                         **metrics})
    pd.DataFrame(rows).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(attacks).to_csv(out / "membership_diagnostic.csv", index=False)
    (out / "privacy_ledger.json").write_text(json.dumps({
        "individual_client_releases": ledgers,
        "sum_epsilons_if_all_private_settings_released_per_client_same_cell": sum(EPSILONS),
        "cross_seed_composition": "overlapping Adult records and changed assignment; no campaign-wide DP claim",
        "fixed_membership_size_assumption": "individual release only; data-dependent assignment is outside guarantee",
        "full_pipeline_dp": False, "deterministic_noise_seed_exposed": False,
        "synthetic_sampling_seeds_public_postprocessing": True,
    }, indent=2) + "\n")
    (out / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256((cell / "partition_manifest.csv").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "histogram_script_sha256": hashlib.sha256((ROOT / "scripts/public_atom_histogram.py").read_bytes()).hexdigest(),
        "rows_per_synthetic_draw": ROWS, "replicates": REPEATS,
        "epsilon_settings": list(EPSILONS), "bins": 8,
        "zero_atom_columns": ["capital-gain", "capital-loss"],
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
                    and prior.get("script_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                    and prior.get("histogram_script_sha256")
                    == hashlib.sha256((ROOT / "scripts/public_atom_histogram.py").read_bytes()).hexdigest()):
                    continue
                raise RuntimeError(f"Incompatible prior privacy output: {out}")
            if (out / "failure.json").exists():
                raise RuntimeError(f"Prior privacy failure retained: {out}")
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
