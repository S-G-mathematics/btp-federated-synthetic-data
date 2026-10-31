#!/usr/bin/env python3
"""Verify the separately dated writing release; never fit or select a model."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance/documentation_release_20261031.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    release = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(ROOT / "SELECTION_FROZEN.json") != release["preserved_selection_sha256"]:
        raise ValueError("Historical experimental selection changed")
    for item in release["files"]:
        path = ROOT / item["path"]
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Writing artifact differs from release manifest: {item['path']}")
    tex = (ROOT / "theory/proofs.tex").read_text(encoding="utf-8")
    md = (ROOT / "theory/PROOFS.md").read_text(encoding="utf-8")
    tex_labels = re.findall(r"\\begin\{statement\}.*?\\label\{([^}]+)\}", tex)
    md_labels = re.findall(r'<a id="([^"]+)"></a>', md)
    if len(tex_labels) != 27 or len(set(tex_labels)) != 27 or tex_labels != md_labels:
        raise ValueError("LaTeX/readable statement identifiers disagree")
    if len(re.findall(r"\\begin\{proof\}", tex)) != 24:
        raise ValueError("Expected 24 proof environments plus three counterexamples")
    if not (ROOT / "theory/proofs.pdf").read_bytes().startswith(b"%PDF-"):
        raise ValueError("Proof PDF missing or invalid signature")
    with (ROOT / "theory/proof_to_experiment_map.csv").open(newline="", encoding="utf-8") as inp:
        entries = list(csv.DictReader(inp))
    if [r["statement_id"] for r in entries] != [f"T{i:02}" for i in range(1, 30)]:
        raise ValueError("Historical theory register must retain T01–T29 in order")
    # Check new documentation against actual repository paths. Historical source
    # documents retain their original cross-environment paths and are not rewritten.
    link_count = 0
    for relative in release["link_check_documents"]:
        document = ROOT / relative
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if href.startswith(("https:", "http:", "mailto:", "#")):
                continue
            target = href.split("#", 1)[0]
            if target and not (document.parent / target).exists():
                raise ValueError(f"Broken path in {relative}: {href}")
            link_count += 1
    print(json.dumps({"status": "passed", "artifact_hashes": len(release["files"]),
                      "proof_statements": 27, "proof_environments": 24,
                      "historical_theory_items": len(entries), "relative_paths_checked": link_count,
                      "scope": "documentation integrity and identifiers, not mathematical proof or model replay"},
                     indent=2))


if __name__ == "__main__":
    main()
