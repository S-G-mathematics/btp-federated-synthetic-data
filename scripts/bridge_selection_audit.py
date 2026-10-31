"""Recompute the old core-cell policy under the audit-only tie rule.

No model is refitted, no synthetic sample is redrawn, and historical files are
never rewritten. This bridge only reuses the saved per-method Exp 1/2 results.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.run import select_release_method

MANIFEST = ROOT / "reports/core_matrix_audit_20261024/manifest.csv"
OUT = ROOT / "reports/core_selection_bridge_20261024"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    reused = manifest[manifest.status == "reuse_with_selection_bridge"]
    rows = []
    for record in reused.itertuples():
        cell = ROOT / record.cell
        config = json.loads((cell / "configuration.json").read_text())
        if config["reference_role"] != "development_assessment":
            raise ValueError(f"Official test is not bridgeable: {cell}")
        validation = pd.read_csv(cell / "exp01_validation.csv")
        assessment = pd.read_csv(cell / "exp01_test.csv")
        new_winner = select_release_method(validation.to_dict("records"))
        old_winner = json.loads((cell / "STATUS.json").read_text())["winner_validation"]
        allowed = validation[
            validation.access == "released_models_and_permitted_summaries"
        ]
        minimum = allowed.query_linf.min()
        ties = allowed[allowed.query_linf == minimum].method.tolist()
        means = assessment.groupby("method").query_linf.mean()
        if new_winner not in means or old_winner not in means or "size" not in means:
            raise ValueError(f"Missing matched method assessment: {cell}")
        rows.append({
            "cell": record.cell,
            "generator": record.generator,
            "partition": record.partition,
            "k": record.k,
            "split_seed": record.seed,
            "old_code_hash": config["code_hash"],
            "old_winner": old_winner,
            "audit_only_winner": new_winner,
            "winner_changed": old_winner != new_winner,
            "primary_exact_ties": len(ties),
            "tied_methods": "|".join(ties),
            "size_assessment_mean": float(means["size"]),
            "old_policy_assessment_mean": float(means[old_winner]),
            "audit_only_policy_assessment_mean": float(means[new_winner]),
            "audit_only_policy_minus_size": float(
                means[new_winner] - means["size"]
            ),
            "split_manifest_sha256": hashlib.sha256(
                (cell / "partition_manifest.csv").read_bytes()
            ).hexdigest(),
            "synthetic_repeats": int(
                len(assessment[assessment.method == new_winner])
            ),
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "bridge_cells.csv", index=False)
    summary = {
        "cells": len(frame),
        "winner_changes": int(frame.winner_changed.sum()),
        "primary_exact_tie_cells": int((frame.primary_exact_ties > 1).sum()),
        "audit_only_policy_better_than_size": int(
            (frame.audit_only_policy_minus_size < 0).sum()
        ),
        "mean_audit_only_policy_minus_size": float(
            frame.audit_only_policy_minus_size.mean()
        ),
        "scope": "per-method Exp 1/2 outputs only; old selected downstream stages not reused",
        "official_test_used": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
