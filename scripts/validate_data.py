#!/usr/bin/env python3
"""Validate UCI Adult inputs and write reproducibility manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from btp.data import ALL_COLUMNS, CATEGORICAL, LABEL, build_partition_rule, prepare_splits, read_adult


EXPECTED_TRAIN, EXPECTED_TEST = 32561, 16281


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_ids(ids) -> str:
    payload = "\n".join(sorted(map(str, ids))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def duplicate_groups(frame: pd.DataFrame) -> dict[tuple, list[str]]:
    result: dict[tuple, list[str]] = {}
    for rid, values in zip(frame.index.astype(str), frame.loc[:, ALL_COLUMNS].itertuples(index=False, name=None)):
        result.setdefault(tuple(values), []).append(rid)
    return result


def validate(raw: Path, out: Path, seed: int = 42, k: int = 5) -> dict:
    source = read_adult(raw)
    train_rows = source.loc[source.index.str.startswith("train:")]
    test_rows = source.loc[source.index.str.startswith("test:")]
    assert len(train_rows) == EXPECTED_TRAIN, f"expected {EXPECTED_TRAIN} official train rows; got {len(train_rows)}"
    assert len(test_rows) == EXPECTED_TEST, f"expected {EXPECTED_TEST} official test rows; got {len(test_rows)}"
    assert len(source) == 48842 and tuple(source.columns) == ALL_COLUMNS
    assert set(source[LABEL].unique()) == {"<=50K", ">50K"}, "labels must be normalized and contain both classes"
    assert not source[LABEL].astype(str).str.endswith(".").any(), "label has unstripped trailing period"
    missing = {col: int((source[col].astype(str) == "?").sum()) for col in CATEGORICAL}

    splits = prepare_splits(raw, seed=seed)
    ids = [str(rid) for frame in splits.values() for rid in frame.index]
    assert len(ids) == len(set(ids)) == 48842, "split row IDs must be a disjoint full cover"
    # Exact full-record duplicate groups may not cross any split boundary.
    all_groups = duplicate_groups(source)
    membership = {str(rid): name for name, frame in splits.items() for rid in frame.index}
    for group in all_groups.values():
        member_splits = {membership[rid] for rid in group}
        # The only cross-boundary group allowed is an official train/test
        # duplicate: its training occurrences are quarantined by policy.
        if "test" in member_splits:
            assert member_splits <= {"test", "quarantine"}, f"test duplicate leaked into development: {group}"
        else:
            assert len(member_splits) == 1, f"development duplicate group split across boundaries: {group}"

    out.parent.mkdir(parents=True, exist_ok=True)
    split_manifest_path = out.parent / "split_manifest.csv"
    pd.DataFrame([(str(rid), name) for name, frame in splits.items() for rid in frame.index],
                 columns=["row_id", "split"]).sort_values("row_id").to_csv(split_manifest_path, index=False)

    partition_manifest = {"seed": seed, "k": k, "fit_split": "train", "assignment_rule": "same rule applied to every split; no evaluation refitting", "partitions": {}}
    for kind in ("age", "age_education", "label_skew"):
        rule = build_partition_rule(splits["train"], k=k, kind=kind, seed=seed)
        per_split = {}
        for name, frame in splits.items():
            assignments = rule.assign(frame)
            per_split[name] = {str(client): int((assignments == client).sum()) for client in range(k)}
        partition_manifest["partitions"][kind] = per_split
    partition_path = out.parent / "client_partition_manifest.json"
    partition_path.write_text(json.dumps(partition_manifest, indent=2, sort_keys=True) + "\n")

    raw_hashes = {str(p.relative_to(raw)): sha256_file(p) for p in sorted(raw.rglob("*")) if p.is_file()}
    manifest = {
        "dataset": "UCI Adult (Census Income)",
        "provenance": {
            "citation": "Becker, B. & Kohavi, R. (1996). Adult [Dataset]. UCI Machine Learning Repository.",
            "doi": "10.24432/C5XW20",
            "url": "https://archive.ics.uci.edu/dataset/2/adult",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "changes": "Whitespace normalized; test label period removed; '?' retained as categorical missing value; exact train records overlapping official test quarantined; remaining official train duplicate groups split into development subsets.",
        },
        "source_rows": {"official_train": len(train_rows), "official_test": len(test_rows), "total": len(source)},
        "columns": list(ALL_COLUMNS),
        "labels": {str(k): int(v) for k, v in source[LABEL].value_counts().sort_index().items()},
        "categorical_question_mark_counts": missing,
        "raw_sha256": raw_hashes,
        "split_seed": seed,
        "split_rows": {name: int(len(frame)) for name, frame in splits.items()},
        "split_row_id_sha256": {name: sha256_ids(frame.index) for name, frame in splits.items()},
        "duplicate_groups": {"count": len(all_groups), "multirow_groups": sum(len(g) > 1 for g in all_groups.values()), "development_cross_split_groups": 0, "train_test_overlap_groups_quarantined": sum("test:" in " ".join(g) and any(r.startswith("train:") for r in g) for g in all_groups.values())},
        "split_manifest_csv": split_manifest_path.name,
        "client_partition_manifest": partition_path.name,
        "client_partition_k": k,
    }
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"), help="directory containing official UCI Adult raw files")
    parser.add_argument("--out", type=Path, default=Path("data/data_manifest.json"), help="manifest JSON path; companion CSV/JSON files go beside it")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clients", type=int, default=5)
    args = parser.parse_args()
    manifest = validate(args.raw, args.out, args.seed, args.clients)
    print(json.dumps({"status": "ok", "source_rows": manifest["source_rows"], "split_rows": manifest["split_rows"], "manifest": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
