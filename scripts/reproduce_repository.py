"""Lightweight saved-result reproduction for the research repository."""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summaries() -> None:
    out = ROOT / "results/summaries/primary_comparison.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["evidence_stage", "dataset", "source_path", "source_sha256", "row_count", "paired_mean_delta", "practical_gain_slices", "registered_margin"])
        for stage, dataset, relative, key in [
            ("adult_development", "Adult", "AUTHOR_READY/PAPER_TABLES/adult_development_slices.csv", "mean_paired_delta"),
            ("adult_confirmation", "Adult", "AUTHOR_READY/PAPER_TABLES/adult_confirmation_slices.csv", "constrained_minus_size"),
            ("external_bank", "Bank Marketing", "AUTHOR_READY/PAPER_TABLES/bank_external_slices.csv", "mean_constrained_minus_size"),
        ]:
            source = ROOT / relative
            with source.open(newline="", encoding="utf-8") as inp:
                rows = list(csv.DictReader(inp))
            if stage == "adult_development":
                rows = [r for r in rows if r["method"] == "constrained" and r["generator"] in {"copula", "chow_liu", "mixed_gmm"}]
            values = [float(r[key]) for r in rows]
            writer.writerow([stage, dataset, relative, sha(source), len(rows), sum(values) / len(values), sum(v <= -0.005 for v in values), -0.005])
    print(out)
    source = ROOT / "AUTHOR_READY/CLAIM_TO_EVIDENCE.csv"
    target = ROOT / "results/summaries/claim_to_evidence.csv"
    with source.open(newline="", encoding="utf-8") as f:
        claims = list(csv.DictReader(f))
    fields = ["claim_id", "claim_text", "experiment_id", "evidence_paths", "metric", "aggregation_rule", "supporting_value", "scope", "limitations", "evidence_stage", "verification_status"]
    experiment_numbers = [1, 1, 1, 2, 4, 3, 5, 6, 7, 8, 9, 10, 11, 12, 12, 12]
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, claim in enumerate(claims, 1):
            paths = []
            for raw in claim["exact_table_or_result_path"].split(";"):
                path = raw.strip()
                path = path if path.startswith("AUTHOR_READY/") else "AUTHOR_READY/" + path
                if not (ROOT / path).is_file():
                    raise FileNotFoundError(path)
                paths.append(path)
            writer.writerow({"claim_id": f"C{i:03d}", "claim_text": claim["retained_claim"],
                             "experiment_id": experiment_numbers[i - 1], "evidence_paths": ";".join(paths),
                             "metric": claim["metric_or_result"], "aggregation_rule": "see cited table caption",
                             "supporting_value": claim["metric_or_result"], "scope": claim["dataset_data_role"],
                             "limitations": claim["dependence_uncertainty_caveat"],
                             "evidence_stage": "saved historical evidence; packaging mapping",
                             "verification_status": "source paths verified by saved-result builder"})
    print(target)


def figures() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    subprocess.run([sys.executable, str(ROOT / "scripts/build_final_reports.py"), "--build"], cwd=ROOT, check=True)
    target = ROOT / "figures/main"
    target.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "reports/final_build").glob("*.png"):
            shutil.copy2(source, target / source.name)
    plots = [
        ("adult_18_slice_differences", "AUTHOR_READY/PAPER_TABLES/adult_development_slices.csv", "mean_paired_delta", "Adult corrected development; 18 slices"),
        ("adult_frozen_confirmation", "AUTHOR_READY/PAPER_TABLES/adult_confirmation_slices.csv", "constrained_minus_size", "Adult frozen official holdout; 6 slices"),
        ("bank_external_slice_differences", "AUTHOR_READY/PAPER_TABLES/bank_external_slices.csv", "mean_constrained_minus_size", "Bank external replication; 4 slices"),
    ]
    for name, relative, column, title in plots:
        with (ROOT / relative).open(newline="", encoding="utf-8") as inp:
            rows = list(csv.DictReader(inp))
        if name.startswith("adult_18"):
            rows = [r for r in rows if r["method"] == "constrained" and r["generator"] in {"copula", "chow_liu", "mixed_gmm"}]
        if name.startswith("bank_"):
            labels = [f"{r['generator']}\n{r['partition']}" for r in rows]
        elif name.startswith("adult_18"):
            labels = [f"{r['generator']} / {r['partition']} / K{r['k']}" for r in rows]
        else:
            labels = [f"{r['partition']} / K{r['k']}" for r in rows]
        values = [float(r[column]) for r in rows]
        fig, ax = plt.subplots(figsize=(9, max(3.2, len(rows) * 0.36 + 1.5)))
        colors = ["#376B9B" if v < 0 else "#C95545" for v in values]
        if name.startswith("bank_"):
            ax.bar(range(len(rows)), values, color=colors)
            ax.set_xticks(range(len(rows)), labels)
            ax.set_ylabel("Query-max Δ (constrained − size)")
            ax.axhline(-0.005, color="black", linestyle="--", linewidth=1, label="registered practical gain")
            ax.axhline(0, color="gray", linewidth=0.7)
        else:
            ax.barh(range(len(rows)), values, color=colors)
            ax.set_yticks(range(len(rows)), labels)
            ax.invert_yaxis()
            ax.set_xlabel("Constrained − size query maximum; lower favours constrained")
            ax.axvline(-0.005, color="black", linestyle="--", linewidth=1, label="registered practical gain")
            ax.axvline(0, color="gray", linewidth=0.7)
        ax.set_title(title)
        ax.legend(loc="best")
        fig.tight_layout()
        for suffix in ("png", "pdf", "svg"):
            fig.savefig(target / f"{name}.{suffix}", dpi=180, bbox_inches="tight")
            if suffix == "svg":
                svg = target / f"{name}.svg"
                svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
        plt.close(fig)
    print(target)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tables", action="store_true", help="run original saved-result report builder and primary summary")
    ap.add_argument("--figures", action="store_true", help="copy verified author figures into the gallery")
    args = ap.parse_args()
    if not args.tables and not args.figures:
        ap.error("specify --tables or --figures")
    if args.tables:
        subprocess.run([sys.executable, str(ROOT / "scripts/build_final_reports.py"), "--build"], cwd=ROOT, check=True)
        summaries()
    if args.figures:
        figures()


if __name__ == "__main__":
    main()
