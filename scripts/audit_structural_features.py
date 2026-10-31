"""Privileged diagnostic of structural Adult features in size-weight samples.

This never changes a generator or supplies real records to server fitting.
The education-number map is learned from development TRAIN for evaluation only.
"""

from __future__ import annotations

import fcntl
import argparse
import hashlib
import json
import os
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, NUMERIC, prepare_splits
from btp.evaluation import sample_mixture
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP

MANIFEST = ROOT / "reports/core_matrix_audit_20261024/manifest.csv"
OUT = ROOT / "reports/structural_features_20261024"
ROWS = 10000


def parts_from_manifest(cell: Path, cfg: dict) -> tuple[list[pd.DataFrame], dict, pd.DataFrame]:
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat(
        [splits[name] for name in ("train", "tune", "calibration", "validation")]
    )
    manifest = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    if not manifest.row_id.isin(development.index).all():
        raise ValueError(f"Split manifest mismatch: {cell}")
    joined = manifest.join(development, on="row_id", validate="one_to_one")
    groups = [
        joined[(joined.split == "test") & (joined.client == i)][
            list(ALL_COLUMNS)
        ].copy()
        for i in range(cfg["k"])
    ]
    train_mapping = (
        splits["train"].groupby("education")["education-num"]
        .agg(lambda x: int(x.mode().iloc[0]))
        .to_dict()
    )
    if cfg.get("workload_version") == "projected_v2":
        if train_mapping != PUBLIC_EDUCATION_NUMBER_MAP:
            raise ValueError("Public education mapping differs from development TRAIN")
        mapping = PUBLIC_EDUCATION_NUMBER_MAP
    else:
        mapping = train_mapping
    return groups, mapping, splits["train"]


def weighted_rate(
    groups: list[pd.DataFrame], alpha: np.ndarray, column: str, value: int,
) -> float:
    return float(sum(
        weight * (group[column] == value).mean()
        for weight, group in zip(alpha, groups)
    ))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lane = Path(os.path.expanduser(resources["shared_compute_lease"]))
    with lane.open("a+") as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Shared heavy-compute lease occupied")
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
        manifest = pd.read_csv(args.manifest)
        rows = []
        for item in manifest.itertuples():
            cell = ROOT / item.cell
            cfg = json.loads((cell / "configuration.json").read_text())
            if cfg["reference_role"] != "development_assessment":
                raise ValueError("Official test is outside this audit")
            summary = np.load(cell / "releases/permitted_summary.npz")
            alpha = summary["alpha"]
            real_parts, education_map, train = parts_from_manifest(cell, cfg)
            models = [
                pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
                for i in range(cfg["k"])
            ]
            synthetic, counts = sample_mixture(
                models, alpha, ROWS, cfg["seed"] + 5200
            )
            if counts.sum() != ROWS:
                raise RuntimeError(f"Exact allocation failed: {cell}")
            expected_num = synthetic.education.map(education_map)
            relation_mismatch = float(
                (expected_num.isna() | (synthetic["education-num"] != expected_num))
                .mean()
            )
            numeric_values = synthetic[list(NUMERIC)].apply(
                pd.to_numeric, errors="coerce"
            ).to_numpy(dtype=float)
            numeric_invalid = float(
                (
                    (~np.isfinite(numeric_values))
                    | (numeric_values != np.rint(numeric_values))
                ).any(axis=1).mean()
            )
            tune_errors = []
            for i in range(cfg["k"]):
                tune = json.loads(
                    (cell / "client_private" / f"tuning_{i}.json").read_text()
                )
                selected = tune["selected"]
                chosen = [
                    trial for trial in tune["trials"]
                    if trial.get("parameters") == selected
                    and trial.get("status") == "eligible"
                ]
                if len(chosen) != 1:
                    raise ValueError(f"Selected local tune trial ambiguous: {cell}")
                tune_errors.append(chosen[0]["local_tune_query_mae"])
            row = {
                "cell": item.cell,
                "generator": item.generator,
                "partition": item.partition,
                "k": item.k,
                "split_seed": item.seed,
                "train_tune_query_mae_client_mean": float(np.mean(tune_errors)),
                "numeric_noninteger_or_nonfinite_row_rate": numeric_invalid,
                "education_number_relation_mismatch_synthetic": relation_mismatch,
                "education_number_relation_mismatch_real_train": float(
                    train["education-num"].ne(
                        train.education.map(education_map)
                    ).mean()
                ),
                "rows": ROWS,
            }
            for column in ("capital-gain", "capital-loss"):
                real_zero = weighted_rate(real_parts, alpha, column, 0)
                synth_zero = float((synthetic[column] == 0).mean())
                row[f"{column}_real_zero_alpha"] = real_zero
                row[f"{column}_synthetic_zero_size"] = synth_zero
                row[f"{column}_zero_error"] = synth_zero - real_zero
            rows.append(row)
        frame = pd.DataFrame(rows)
        frame.to_csv(args.out / "cell_diagnostics.csv", index=False)
        summary = (
            frame.groupby(["generator", "partition", "k"])
            .agg(
                split_seeds=("split_seed", "nunique"),
                capital_gain_zero_error_mean=("capital-gain_zero_error", "mean"),
                capital_loss_zero_error_mean=("capital-loss_zero_error", "mean"),
                education_relation_mismatch_mean=(
                    "education_number_relation_mismatch_synthetic", "mean"
                ),
                local_tune_query_mae_mean=(
                    "train_tune_query_mae_client_mean", "mean"
                ),
            )
            .reset_index()
        )
        summary.to_csv(args.out / "slice_summary.csv", index=False)
        (args.out / "configuration.json").write_text(json.dumps({
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_manifest": str(args.manifest.resolve().relative_to(ROOT)),
            "synthetic_rows": ROWS,
            "size_weights": "alpha from TRAIN",
            "reference_role": "development_assessment",
            "mapping_fit_role": "public fixed map verified on development TRAIN for projected_v2; otherwise evaluator TRAIN mode",
            "official_test_used": False,
            "status": "complete",
        }, indent=2) + "\n")
        print("audited", len(frame), "development cells")


if __name__ == "__main__":
    main()
