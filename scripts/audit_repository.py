"""Static, inexpensive audit of the packaged source/evidence repository."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = "2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(relative: str) -> list[dict]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as inp:
        return list(csv.DictReader(inp))


def audit() -> dict:
    if sha(ROOT / "SELECTION_FROZEN.json") != FREEZE:
        raise ValueError("Immutable freeze hash differs")
    inventory = json.loads((ROOT / "provenance/source_inventory.json").read_text())
    manifest = json.loads((ROOT / "artifacts/full_archive_manifest_v2.json").read_text())
    if manifest["file_count"] != 10687 or inventory["full_archive_sha256"] != "b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf":
        raise ValueError("Full archive provenance differs")
    closure = json.loads((ROOT / "EXPERIMENTS_01_TO_12_CLOSURE.json").read_text())
    if len(closure["packages"]) != 12:
        raise ValueError("Incomplete closure register")
    for package in closure["packages"]:
        num = package["experiment"]
        if not list((ROOT / "experiments").glob(f"exp{num:02d}_*/README.md")):
            raise ValueError(f"Experiment guide absent: {num}")
        for evidence in package["evidence"]:
            if not (ROOT / evidence).exists():
                raise ValueError(f"Missing closure evidence: {evidence}")
    mapping = read_csv("provenance/source_to_repository_map.csv")
    tracked: set[str] | None = None
    if (ROOT / ".git").exists():
        result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, check=True)
        tracked = {x.decode("utf-8") for x in result.stdout.split(b"\0") if x}
    for row in mapping:
        target = ROOT / row["repository_path"]
        if not target.is_file():
            raise ValueError(f"Copied source absent: {target}")
        if tracked is not None and row["repository_path"] not in tracked:
            raise ValueError(f"Copied source is not Git-tracked: {row['repository_path']}")
        if target.as_posix().endswith("/README.md") and row["repository_path"] == "README.md":
            continue  # the root landing page is deliberately rewritten for GitHub
        if sha(target) != row["sha256"]:
            raise ValueError(f"Copied source altered: {target}")
    summary = read_csv("results/summaries/primary_comparison.csv")
    expected = {"adult_development": (18, 0, 0.002427902586662067),
                "adult_confirmation": (6, 0, -0.00021490707600188447),
                "external_bank": (4, 0, -0.0013317491723437499)}
    for row in summary:
        n, practical, value = expected[row["evidence_stage"]]
        if (int(row["row_count"]) != n or int(row["practical_gain_slices"]) != practical or
                abs(float(row["paired_mean_delta"]) - value) > 1e-9):
            raise ValueError(f"Incorrect primary comparison: {row}")
        if sha(ROOT / row["source_path"]) != row["source_sha256"]:
            raise ValueError("Primary summary source hash differs")
    claims = read_csv("results/summaries/claim_to_evidence.csv")
    if len({r["claim_id"] for r in claims}) != len(claims):
        raise ValueError("Duplicate claim identifiers")
    for row in claims:
        for evidence in row["evidence_paths"].split(";"):
            if not (ROOT / evidence).is_file():
                raise ValueError(f"Missing claim evidence: {evidence}")
    link_count = 0
    guides = [ROOT / "README.md", *ROOT.glob("experiments/exp*/README.md"),
              ROOT / "REPRODUCIBILITY.md", ROOT / "ARTIFACTS.md", ROOT / "theory/README.md",
              ROOT / "theory/statements.md"]
    for guide in guides:
        content = guide.read_text(encoding="utf-8")
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if href.startswith(("http:", "https:", "#")):
                continue
            path = href.split("#", 1)[0]
            if path and not (guide.parent / path).exists():
                raise ValueError(f"Broken relative link in {guide}: {href}")
            link_count += 1
    corrected = json.loads((ROOT / "reports/completion_integrity_20261025/integrity_summary.json").read_text())
    for key, value in (("cells", 57), ("core_cells", 54), ("method_rows", 741), ("assessment_draw_rows", 3705), ("certified_fixed_pilot_lps", 57)):
        if corrected[key] != value:
            raise ValueError(f"Corrected development count changed: {key}")
    draws = read_csv("reports/final_build/confirmation_all_draws.csv")
    if len(draws) != 180:
        raise ValueError("Expected 180 frozen confirmation draw metric rows")
    bank = read_csv("reports/external_replication/all_draws.csv")
    if len(bank) != 180:
        raise ValueError("Expected 180 Bank draw metric rows")
    return {"status": "passed", "closure_packages": 12, "source_copies_hashed": len(mapping),
            "claims_linked": len(claims), "relative_links_checked": link_count, "primary_summary_rows": 3,
            "adult_confirmation_draw_metric_rows": len(draws), "bank_draw_metric_rows": len(bank)}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
