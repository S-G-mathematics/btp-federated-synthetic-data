"""Audit reuse and missing cells for the three-generator 54-cell core."""

from __future__ import annotations

import hashlib
import itertools
import json
from datetime import datetime
from pathlib import Path
from statistics import median

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/core_matrix_audit_20261024"
GENERATORS = ("copula", "chow_liu", "mixed_gmm")
PARTITIONS = ("age", "age_education", "label_skew")
CLIENTS = (5, 10)
SEEDS = (101, 202, 303)
BRIDGE_HASH = "ff7cd479d151"
BRIDGE_ROOTS = {
    "ec2_copula_seed101_current_code_20261024",
    "ec2_copula_replication_20261024",
    "ec2_chow_gmm_replication_20261024",
}
EXP12_PROFILE_KEYS = (
    "smoke", "severity", "pilot_samples", "tune_samples", "synthetic_rows",
    "support_size", "barycenter_weight_trials", "kernel_features", "repeats",
)


def code_hash() -> str:
    h = hashlib.sha256()
    for path in sorted((ROOT / "btp").glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def elapsed_seconds(cell: Path) -> float | None:
    log = cell / "execution.log"
    if not log.exists():
        return None
    lines = log.read_text().splitlines()
    if len(lines) < 2:
        return None
    try:
        start = datetime.fromisoformat(lines[0].split(" ", 1)[0])
        end = datetime.fromisoformat(lines[-1].split(" ", 1)[0])
        value = (end - start).total_seconds()
        return value if value > 0 else None
    except (ValueError, IndexError):
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    current_hash = code_hash()
    current_profile = yaml.safe_load((ROOT / "configs/campaign.yaml").read_text())[
        "profiles"
    ]["pilot"]
    cells: dict[tuple, list[dict]] = {}
    for config_path in (ROOT / "results").glob("*/**/configuration.json"):
        try:
            config = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        key = (
            config.get("generator"), config.get("partition"),
            config.get("k"), config.get("seed"),
        )
        if (
            key[0] not in GENERATORS or key[1] not in PARTITIONS
            or key[2] not in CLIENTS or key[3] not in SEEDS
        ):
            continue
        cell = config_path.parent
        if not (cell / "exp02_complete.json").exists():
            continue
        matching_profile = all(
            config.get("profile", {}).get(name) == current_profile.get(name)
            for name in EXP12_PROFILE_KEYS
        )
        valid_reference = config.get("reference_role") == "development_assessment"
        oracle = json.loads((cell / "exp02_oracle.json").read_text())
        valid_oracle = bool(oracle["solver"]["success"])
        weight_fits = json.loads((cell / "weight_fits.json").read_text())
        fits = weight_fits["methods"]
        all_fits = all(bool(fit.get("success")) for fit in fits)
        record = {
            "cell": str(cell.relative_to(ROOT)),
            "root": cell.parent.name,
            "code_hash": config["code_hash"],
            "profile_matches_exp12": matching_profile,
            "reference_ok": valid_reference,
            "oracle_ok": valid_oracle,
            "all_method_fits_ok": all_fits,
            "method_fit_count": len(fits),
            "elapsed_seconds": elapsed_seconds(cell),
            "raw_sha256": config["raw_sha256"],
            "split_manifest_sha256": hashlib.sha256(
                (cell / "partition_manifest.csv").read_bytes()
            ).hexdigest(),
        }
        cells.setdefault(key, []).append(record)

    rows = []
    durations: dict[tuple[str, int], list[float]] = {}
    for gen, part, k, seed in itertools.product(
        GENERATORS, PARTITIONS, CLIENTS, SEEDS
    ):
        key = (gen, part, k, seed)
        options = cells.get(key, [])
        exact = [
            x for x in options
            if x["code_hash"] == current_hash and x["profile_matches_exp12"]
            and x["reference_ok"] and x["oracle_ok"] and x["all_method_fits_ok"]
        ]
        bridge = [
            x for x in options
            if x["code_hash"].startswith(BRIDGE_HASH)
            and x["root"] in BRIDGE_ROOTS
            and x["profile_matches_exp12"] and x["reference_ok"]
            and x["oracle_ok"] and x["all_method_fits_ok"]
        ]
        if exact:
            chosen, status = exact[0], "complete_exact"
        elif bridge:
            chosen, status = bridge[0], "reuse_with_selection_bridge"
        elif options:
            chosen, status = options[0], "rerun_incompatible_history"
        else:
            chosen, status = {}, "missing"
        if chosen.get("elapsed_seconds"):
            durations.setdefault((gen, k), []).append(chosen["elapsed_seconds"])
        rows.append({
            "generator": gen, "partition": part, "k": k, "seed": seed,
            "status": status, "cell": chosen.get("cell", ""),
            "code_hash": chosen.get("code_hash", ""),
            "exp12_profile_matches": chosen.get("profile_matches_exp12", False),
            "oracle_ok": chosen.get("oracle_ok", False),
            "all_method_fits_ok": chosen.get("all_method_fits_ok", False),
            "method_fit_count": chosen.get("method_fit_count", 0),
            "elapsed_seconds": chosen.get("elapsed_seconds"),
            "split_manifest_sha256": chosen.get("split_manifest_sha256", ""),
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "manifest.csv", index=False)
    run_rows = frame[frame.status.isin(("missing", "rerun_incompatible_history"))]
    medians = {
        f"{gen}_k{k}": round(median(values), 1)
        for (gen, k), values in durations.items()
    }
    estimated = 0.0
    for row in run_rows.itertuples():
        estimated += median(durations.get((row.generator, row.k), [120.0]))
    summary = {
        "current_code_hash": current_hash,
        "pilot_profile_exp12_keys": list(EXP12_PROFILE_KEYS),
        "counts": frame.status.value_counts().to_dict(),
        "measured_median_cell_seconds": medians,
        "estimated_remaining_sequential_seconds": round(estimated),
        "estimate_scope": "median completed-cell wall durations; not a resource guarantee",
        "bridge_scope": "old per-method Exp1/2 results; recompute the selection-policy summary, do not reuse old selected downstream stages",
        "official_test_used": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
