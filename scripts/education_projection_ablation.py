"""Matched postpilot Adult education-number projection ablation.

The fixed category-to-code map is explicitly declared here and verified on
development TRAIN only. This postprocessing experiment does not redefine a
client model's log score or turn any nonprivate release into a DP mechanism.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import prepare_splits
from btp.evaluation import empirical_metrics, public_workloads, sample_mixture
from btp.privacy import public_schema
from representation_constrained import reference_parts

EDUCATION_NUM_MAP = {
    "Preschool": 1,
    "1st-4th": 2,
    "5th-6th": 3,
    "7th-8th": 4,
    "9th": 5,
    "10th": 6,
    "11th": 7,
    "12th": 8,
    "HS-grad": 9,
    "Some-college": 10,
    "Assoc-voc": 11,
    "Assoc-acdm": 12,
    "Bachelors": 13,
    "Masters": 14,
    "Prof-school": 15,
    "Doctorate": 16,
}
ROWS = 10000
REPEATS = 5


def verify_train_mapping(seed: int) -> None:
    train = prepare_splits(ROOT / "data/raw", seed)["train"]
    encoded = train.education.map(EDUCATION_NUM_MAP)
    if encoded.isna().any() or not (encoded == train["education-num"]).all():
        raise ValueError("Declared mapping fails development TRAIN verification")


def run_cell(cell: Path, output: Path) -> None:
    cfg = json.loads((cell / "configuration.json").read_text())
    if cfg["reference_role"] != "development_assessment":
        raise ValueError("Official test is outside this ablation")
    verify_train_mapping(cfg["seed"])
    source = ROOT / "results/representation_constrained_20261024" / cell.name
    fit = json.loads((source / "weight_fits.json").read_text())
    source_config = json.loads((source / "configuration.json").read_text())
    if source_config["status"] != "complete" or source_config["official_test_used"]:
        raise ValueError(f"Incompatible constrained source: {source}")
    summary = np.load(cell / "releases/permitted_summary.npz")
    alpha = summary["alpha"]
    parts = reference_parts(cell, cfg, alpha)
    models = [
        pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
        for i in range(cfg["k"])
    ]
    workload, audit = public_workloads(public_schema())
    records = []
    for method in ("size", "constrained"):
        weights = np.asarray(fit[method]["weights"], float)
        for rep in range(REPEATS):
            seed = cfg["seed"] + 5200 + rep
            synthetic, counts = sample_mixture(models, weights, ROWS, seed)
            if counts.sum() != ROWS:
                raise RuntimeError("Synthetic largest-remainder allocation failed")
            encoded = synthetic.education.map(EDUCATION_NUM_MAP)
            unsupported = encoded.isna()
            unsupported_rate = float(unsupported.mean())
            before_mismatch = float(
                (unsupported | (synthetic["education-num"] != encoded)).mean()
            )
            projected = synthetic.copy()
            projected.loc[~unsupported, "education-num"] = (
                encoded.loc[~unsupported].astype(int)
            )
            after_mismatch = float(
                (unsupported | (projected["education-num"] != encoded)).mean()
            )
            for status, frame, mismatch in (
                ("raw_model_sample", synthetic, before_mismatch),
                ("mapped_education_number", projected, after_mismatch),
            ):
                metrics = empirical_metrics(
                    parts["test"], frame, workload, audit, alpha
                )
                records.append({
                    "method": method,
                    "projection": status,
                    "replicate": rep,
                    "sample_seed": seed,
                    "education_relation_mismatch": mismatch,
                    "unmapped_education_rate": unsupported_rate,
                    **metrics,
                })
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(output / "metrics.csv", index=False)
    (output / "configuration.json").write_text(json.dumps({
        "source_cell": str(cell.relative_to(ROOT)),
        "source_code_hash": cfg["code_hash"],
        "source_manifest_sha256": hashlib.sha256(
            (cell / "partition_manifest.csv").read_bytes()
        ).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "mapping": EDUCATION_NUM_MAP,
        "mapping_role": "fixed postpilot declaration verified on development TRAIN only; unknown education stays unprojected and is counted unsupported",
        "projected_score_claim": "none; original generator scores describe preprojection rows",
        "rows": ROWS,
        "repeats": REPEATS,
        "reference_role": cfg["reference_role"],
        "official_test_used": False,
        "status": "complete",
        "ended_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(cell.name, "complete", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path,
        default=ROOT / "reports/core_matrix_audit_20261024/manifest.csv",
    )
    parser.add_argument(
        "--out", type=Path,
        default=ROOT / "results/education_projection_ablation_fixed_20261024",
    )
    parser.add_argument("--max-cells", type=int, default=6)
    args = parser.parse_args()
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lane = Path(os.path.expanduser(resources["shared_compute_lease"]))
    lane.parent.mkdir(parents=True, exist_ok=True)
    with lane.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
        started = time.monotonic()
        completed = 0
        manifest = pd.read_csv(args.manifest)
        for item in manifest.itertuples():
            if completed >= args.max_cells:
                break
            if time.monotonic() - started >= resources["campaign_wall_seconds"]:
                break
            cell = ROOT / item.cell
            output = args.out / cell.name
            marker = output / "configuration.json"
            failure = output / "failure.json"
            if marker.exists():
                previous = json.loads(marker.read_text())
                if (
                    previous.get("status") == "complete"
                    and previous.get("script_sha256")
                    == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                    and previous.get("source_manifest_sha256")
                    == hashlib.sha256(
                        (cell / "partition_manifest.csv").read_bytes()
                    ).hexdigest()
                ):
                    continue
                raise RuntimeError(f"Incompatible previous output: {output}")
            if failure.exists():
                raise RuntimeError(f"Previous failure retained: {failure}")
            mem = Path("/proc/meminfo").read_text()
            available = next(
                int(line.split()[1]) * 1024 for line in mem.splitlines()
                if line.startswith("MemAvailable:")
            )
            if (
                available < resources["minimum_available_ram_gib"] * 2**30
                or shutil.disk_usage(ROOT).free
                < resources["minimum_free_disk_gib"] * 2**30
            ):
                raise RuntimeError("Shared resource reserve reached")
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
