"""Fail-closed gate for the campaign-wide Adult official-test confirmation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED = (
    "project", "protocol_version", "created_at_utc", "purpose", "retained_claim",
    "selected_generator", "candidate_families", "selection_rule",
    "local_tuning", "preprocessing", "target", "partitions", "main_weight_rule",
    "challenger", "primary_workload", "audit_workload", "synthetic_draws",
    "random_substreams", "conditional_policy", "predictive_policy", "baselines",
    "metrics", "pilot_oracle", "software", "inputs", "confirmation_commands",
    "reporting_change_policy", "code_fix_invalidation_policy", "alternatives_considered",
    "known_limitations", "assessment_informed_history", "confirmation_seeds",
)


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_freeze(path: Path, root: Path, expected_code_hash: str) -> dict:
    path = Path(path)
    root = Path(root).resolve()
    if not path.is_file():
        raise ValueError("Campaign-wide SELECTION_FROZEN.json is missing")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(freeze, dict):
        raise ValueError("Freeze must be a JSON object")
    missing = [k for k in REQUIRED if k not in freeze or freeze[k] in (None, "", [], {})]
    if missing:
        raise ValueError(f"Incomplete freeze fields: {missing}")
    for key, expected in {
        "global_freeze_complete": True, "test_used_for_selection": False,
        "confirmation_seeds_used_for_selection": False, "assessment_informed_design": True,
        "main_pipeline_private": False,
    }.items():
        if freeze.get(key) is not expected:
            raise ValueError(f"Invalid freeze gate flag {key}")
    if freeze["selected_generator"] not in ("copula", "chow_liu", "mixed_gmm"):
        raise ValueError("Unregistered selected generator")
    if sorted(freeze["candidate_families"]) != ["chow_liu", "copula", "mixed_gmm"]:
        raise ValueError("Candidate family set changed")
    if freeze["confirmation_seeds"] != [404, 505]:
        raise ValueError("Confirmation seed list changed")
    if freeze["main_weight_rule"].get("name") != "size" or freeze["main_weight_rule"].get("formula") != "w=alpha":
        raise ValueError("Main weight rule must be frozen size weighting")
    challenger = freeze["challenger"]
    if challenger.get("delta_l1") != 0.25 or challenger.get("floor_ratio") != 0.5:
        raise ValueError("Representation constraints changed")
    draws = freeze["synthetic_draws"]
    if draws.get("rows") != 10000 or draws.get("repeats") != 5 or draws.get("allocation") != "largest_remainder":
        raise ValueError("Registered synthetic sampling changed")
    if freeze["metrics"].get("practical_improvement_margin") != 0.005:
        raise ValueError("Registered practical margin changed")
    if freeze["software"].get("code_hash") != expected_code_hash:
        raise ValueError("Frozen scoring source hash differs from installed source")
    if not isinstance(freeze["inputs"], dict) or not freeze["inputs"]:
        raise ValueError("Freeze input hash registry is empty")
    for name, entry in freeze["inputs"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError(f"Invalid input hash entry: {name}")
        target = (root / entry["path"]).resolve()
        if not target.is_relative_to(root) or not target.is_file() or sha256(target) != entry["sha256"]:
            raise ValueError(f"Frozen input is missing or hash-mismatched: {name}")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    expected = hashlib.sha256(canonical_bytes(freeze)).hexdigest()
    if not sidecar.is_file() or sidecar.read_text(encoding="ascii").strip() != expected:
        raise ValueError("Freeze canonical SHA-256 sidecar missing or mismatched")
    if path.read_bytes() != canonical_bytes(freeze):
        raise ValueError("Freeze JSON is not in its declared canonical serialization")
    return freeze


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    from btp.run import code_hash
    result = validate_freeze(args.freeze, args.root, code_hash())
    print(json.dumps({"status": "accepted", "selected_generator": result["selected_generator"]}))


if __name__ == "__main__":
    main()
