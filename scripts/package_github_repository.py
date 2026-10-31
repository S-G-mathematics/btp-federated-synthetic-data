"""Stage the audited BTP project for a private research repository.

This is a packaging tool: it never fits models or reads official-test rows.
Run on the verified EC2 project with an empty, explicitly chosen destination.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA = "b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf"
FREEZE_SHA = "2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23"
STAGE = {1: "development and frozen confirmation", 2: "finite-pilot development",
         3: "algebraic identity", 4: "development sample-size audit",
         5: "development and frozen confirmation", 6: "development and frozen confirmation",
         7: "development predictor audit", 8: "development and frozen confirmation",
         9: "development mechanisms", 10: "development severity mechanism",
         11: "finite empirical transfer audit", 12: "development privacy/resource audit"}
SLUGS = {
    1: "fixed_target_weighting", 2: "pilot_optimality", 3: "subset_composition",
    4: "synthetic_sample_size", 5: "conditional_generation", 6: "downstream_utility",
    7: "joint_implied_prediction", 8: "query_diagnostics", 9: "controlled_ablations",
    10: "heterogeneity", 11: "conditional_transfer", 12: "privacy_and_resources",
}
FAMILY = {
    1: "copula, Chow-Liu, mixed GMM; independent controls; size, uniform and registered statistical challengers",
    2: "fixed local checkpoints; finite-pilot mixture LP and fresh-sample checks",
    3: "no fitting; mixtures over overlapping client subsets",
    4: "fixed saved generators and size/registered weighting comparisons",
    5: "direct teacher rejection and separately trained per-condition Chow-Liu students",
    6: "synthetic-trained and privileged real-trained logistic regression and extra trees",
    7: "exact supported projected Chow-Liu and approximate GMM/copula score routes",
    8: "frozen synthetic draws and empirical query evaluator",
    9: "same-row projection and fixed-pilot released-summary variants",
    10: "selected copula, equal client quantities and equal target mass",
    11: "finite-query conditional bounds and teacher/student empirical identities",
    12: "conditional private atom histogram, nonprivate PGM, adapted FLAIM, release-payload audit",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, required=True)
    args = ap.parse_args()
    dest = args.dest.expanduser().resolve()
    if dest.exists():
        raise SystemExit(f"Destination exists; refusing overwrite: {dest}")
    archive = ROOT.parent / "BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip"
    if sha(archive) != FULL_SHA or sha(ROOT / "SELECTION_FROZEN.json") != FREEZE_SHA:
        raise SystemExit("Full archive or immutable campaign freeze hash differs")
    closure = json.loads((ROOT / "EXPERIMENTS_01_TO_12_CLOSURE.json").read_text())
    manifest_path = ROOT / "ARTIFACT_SHA256_MANIFEST.json"
    full_manifest = json.loads(manifest_path.read_text())
    archived = {x["path"]: x for x in full_manifest["files"]}
    copied: list[dict] = []
    dest.mkdir(parents=True)

    def cp(src: Path, relative: Path | None = None) -> None:
        rel = relative or src.relative_to(ROOT)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        source_rel = src.relative_to(ROOT).as_posix()
        digest = sha(src)
        item = archived.get(source_rel)
        copied.append({"original_path": source_rel, "repository_path": rel.as_posix(),
                       "bytes": src.stat().st_size, "sha256": digest,
                       "matches_v2_archive": bool(item and item["sha256"] == digest)})

    for folder in ("btp", "scripts", "tests", "configs", "docs", "environment", "reports", "AUTHOR_READY", "logs", "data"):
        for src in sorted((ROOT / folder).rglob("*")):
            if not src.is_file() or any(x in src.parts for x in ("__pycache__", ".pytest_cache", ".venv")):
                continue
            rel = src.relative_to(ROOT)
            if folder == "logs" and (src.suffix not in (".log", ".txt", ".json") or src.stat().st_size > 2_000_000):
                continue
            if folder == "data" and src.suffix not in (".csv", ".json", ".md", ".zip", ".data", ".test", ".names", ".gz"):
                continue
            if folder == "reports" and src.stat().st_size > 10_000_000:
                continue
            if folder == "AUTHOR_READY" and src.suffix.lower() in (".aux", ".log"):
                continue
            cp(src)
    for src in sorted((ROOT / "results").rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        # Textual cell outputs are the canonical saved evidence used by report builders.
        # Checkpoints and large per-record/draw artifacts remain in the verified full archive.
        if src.suffix.lower() in (".csv", ".json", ".txt", ".yaml", ".yml", ".md", ".log", ".svg") and src.stat().st_size <= 5_000_000:
            cp(src)
    for src in sorted(ROOT.iterdir()):
        if src.is_file() and src.suffix.lower() in (".md", ".json", ".txt", ".toml", ".bib", ".pdf", ".csv") and src.name not in ("ARTIFACT_SHA256_MANIFEST.json",):
            cp(src)
    (dest / "artifacts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, dest / "artifacts" / "full_archive_manifest_v2.json")

    source_map = dest / "provenance" / "source_to_repository_map.csv"
    source_map.parent.mkdir(parents=True, exist_ok=True)
    with source_map.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(copied[0]))
        w.writeheader(); w.writerows(copied)
    included = {x["original_path"] for x in copied}
    inventory = {
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root_ec2": str(ROOT), "full_archive_ec2": str(archive),
        "full_archive_sha256": FULL_SHA, "freeze_sha256": FREEZE_SHA,
        "archive_file_count": len(archived), "repository_copied_file_count": len(copied),
        "categories": {
            "present_directly_inspected": "EC2 project paths and executable layout",
            "present_integrity_verified": "full v2 archive hash, frozen selection, copied files with matches_v2_archive=true",
            "referenced_absent": "see artifacts/README.md; no permanent public artifact store asserted",
            "present_not_yet_validated": "individual excluded binary checkpoint loads; original archive manifest retained",
            "fresh_reproductions": "record packaging-time commands in logs/packaging/ after running them",
        },
        "archive_files_not_copied_to_git": [
            {"path": p, "bytes": x["bytes"], "sha256": x["sha256"], "availability": "verified full v2 archive on EC2 and laptop; GitHub release pending"}
            for p, x in archived.items() if p not in included
        ],
    }
    write(dest / "provenance" / "source_inventory.json", json.dumps(inventory, indent=2) + "\n")
    write(dest / "artifacts" / "README.md", f"""# Large artifact access

The complete executable archive is `BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip` (SHA-256 `{FULL_SHA}`). It has model checkpoints, synthetic draws, paired prediction rows and full historical result lineage; `full_archive_manifest_v2.json` lists every member. The verified original is preserved on EC2 at `{archive}` and on the owner's laptop. This repository keeps source and inspectable tables; it does not claim the excluded binaries are downloadable from GitHub unless a release asset is linked here after verification. Only load trusted pickle checkpoints. GitHub source alone regenerates the included tables if their saved input CSVs are present; complete fit/draw replay requires the full archive.

Artifact state and SHA-256 are recorded in `../provenance/source_inventory.json`. No credential or private key belongs in the archive or repository.
""")

    # Experiment guides use the original executable layout and link canonical evidence.
    write(dest / "experiments" / "README.md", "# Twelve bounded work packages\n\nThese guides point into the preserved executable `btp/`, `scripts/`, `configs/`, `results/`, `reports/` and `docs/` layout. Statuses come from the dated closure register. Historical runs are not fresh packaging-time executions.\n")
    for pkg in closure["packages"]:
        i = pkg["experiment"]
        slug = SLUGS[i]
        exp = dest / "experiments" / f"exp{i:02d}_{slug}"
        evidence = [Path(p) for p in pkg["evidence"]]
        links = "\n".join(f"- [{p.as_posix()}](../../{p.as_posix()})" for p in evidence)
        missing = [p.as_posix() for p in evidence if not (dest / p).exists()]
        result = pkg["completed_scope"]
        category = "completed mathematical identity/proof with numerical check" if i == 3 else ("completed bounded audit" if i in (8, 11, 12) else "completed empirical comparison")
        text = f"""# Experiment {i}: {slug.replace('_', ' ').title()}

**Question.** {pkg['question']}

**Hypothesis/objective.** {pkg['retained_claim']}

**Type and status.** {category}; `{pkg['disposition']}` in the dated twelve-package closure. The files linked below record historical execution. This guide is a packaging-time index, not a new experiment.

**Dataset and data roles.** Official UCI Adult is the primary dataset; Experiment 1 additionally includes UCI Bank Marketing `bank-additional-full.csv` as registered external replication. Adult official test was scored only after the campaign freeze. Local fitting uses train/local tune, weighting uses permitted calibration summaries, and a privileged evaluator scores held-out real references. Bank's `duration` is excluded. See [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md) and [freeze](../../SELECTION_FROZEN.json).

**Models and methods.** {FAMILY[i]}. All clients use the same schema. The final Adult generator is train/local-tune-selected projected copula; the main weight comparator uses the fixed alpha target, L1 budget 0.25 and floor 0.5 alpha. Other families or access levels in historical results are labelled separately.

**Partitions, clients and seeds.** The corrected core uses age, age+education and label-skew assignments, K=5/10, seeds 101/202/303. Frozen Adult confirmation uses 404/505; Bank replication uses its registered split and 611/622/633. Experiment-specific subsets, severity seeds, pilot and draw streams are recorded in the linked evidence and [configuration](../../configs/campaign.yaml). Do not infer that all combinations were run in this package.

**Synthetic and pilot budgets.** The primary Adult/Bank comparison uses m=10,000 and five synthetic draws. Exp2 varies pilots 500/1,500/5,000/15,000; Exp4 varies m=2,500/10,000/40,000. Other conditional or private budgets are in their fixed protocols and run manifests.

**Metric and aggregation.** {pkg['metric']}. Lower is better for query error and Brier; higher is better for AUROC/AUPRC. Primary paired contrast is challenger minus size; negative favours challenger. Draws are averaged within a cell before slice/overall summaries. The exact unit for this package is in the evidence tables; seeds and draws reuse people and are not independent cohorts.

**Executable source/configuration.** [Package](../../btp/), [experiment runners](../../scripts/), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt). `python scripts/reproduce_repository.py --tables` rebuilds saved-result reports without fitting. Full historical execution commands and resource limits are in [REPRODUCE](../../REPRODUCE.md); a specific cell must be explicitly selected there. No default command launches a campaign.

**Expected outputs.** Canonical files below, retained report tables in `reports/`, inspectable author tables in `AUTHOR_READY/PAPER_TABLES/`, and full checkpoints/draws in the verified v2 archive manifest. The latter are not silently duplicated in Git.

**Recorded result.** {result}

**Interpretation.** {pkg['retained_claim']}

**Limitations/exclusions.** {pkg['unresolved_scope']}. Forbidden extension: {pkg['forbidden_claim']}

**Evidence stage.** {STAGE[i]}. Historical source files are retained, and packaging-time checks appear separately in `logs/packaging/` when run. Missing in-Git evidence links: {', '.join(missing) if missing else 'none'}.

**Canonical evidence and provenance.**\n{links}\n
See [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [full archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
"""
        write(exp / "README.md", text)
    make_summaries(dest, closure)
    make_docs(dest)
    print(json.dumps({"destination": str(dest), "copied_files": len(copied),
                      "copied_bytes": sum(x["bytes"] for x in copied),
                      "archive_only_files": len(inventory["archive_files_not_copied_to_git"])}, indent=2))


def make_summaries(dest: Path, closure: dict) -> None:
    out = dest / "results" / "summaries"
    out.mkdir(parents=True, exist_ok=True)
    fields = ("experiment_id", "question", "methods_and_scope", "metric", "result", "status", "evidence_paths", "limitations")
    with (out / "experiment_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fields)
        for x in closure["packages"]:
            w.writerow([x["experiment"], x["question"], x["methods_and_scope"], x["metric"],
                        x["completed_scope"], x["disposition"], ";".join(x["evidence"]), x["unresolved_scope"]])
    files = [
        ("adult_development", "AUTHOR_READY/PAPER_TABLES/adult_development_slices.csv"),
        ("adult_confirmation", "AUTHOR_READY/PAPER_TABLES/adult_confirmation_slices.csv"),
        ("external_bank", "AUTHOR_READY/PAPER_TABLES/bank_external_slices.csv"),
    ]
    with (out / "primary_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["evidence_stage", "dataset", "source_path", "source_sha256", "row_count", "paired_mean_delta", "practical_gain_slices", "registered_margin"])
        for stage, rel in files:
            src = dest / rel
            with src.open(newline="", encoding="utf-8") as inp:
                rows = list(csv.DictReader(inp))
            if stage == "adult_development":
                rows = [r for r in rows if r["method"] == "constrained" and r["generator"] in ("copula", "chow_liu", "mixed_gmm")]
            cols = rows[0].keys()
            delta = next((c for c in cols if c in ("mean_paired_delta", "mean_constrained_minus_size", "constrained_minus_size")), None)
            if delta is None:
                raise ValueError(f"No paired delta column in {rel}: {list(cols)}")
            vals = [float(r[delta]) for r in rows]
            w.writerow([stage, "Bank Marketing" if stage == "external_bank" else "Adult", rel, sha(src), len(rows),
                        sum(vals) / len(vals), sum(v <= -0.005 for v in vals), -0.005])
    source = dest / "AUTHOR_READY" / "CLAIM_TO_EVIDENCE.csv"
    with source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with (out / "claim_to_evidence.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["claim_id", "claim_text", "experiment_id", "evidence_paths", "metric", "aggregation_rule", "supporting_value", "scope", "limitations", "evidence_stage", "verification_status"]
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for i, row in enumerate(rows, 1):
            p = row["exact_table_or_result_path"]
            w.writerow({"claim_id": f"C{i:03d}", "claim_text": row["retained_claim"], "experiment_id": "",
                        "evidence_paths": "AUTHOR_READY/" + p, "metric": row["metric_or_result"],
                        "aggregation_rule": "see cited table caption", "supporting_value": row["metric_or_result"],
                        "scope": row["dataset_data_role"], "limitations": row["dependence_uncertainty_caveat"],
                        "evidence_stage": "saved historical evidence; packaging mapping", "verification_status": "source hash and path to be audited"})


def make_docs(dest: Path) -> None:
    summary = json.loads((dest / "reports/final_build/summary.json").read_text())
    write(dest / ".gitignore", ".venv/\n__pycache__/\n.pytest_cache/\n*.pyc\n*.pkl\n*.npz\n*.parquet\n*.tmp\n.env\n.env.*\n*.pem\n*.key\n*.p12\n*.pfx\n*token*\n*secret*\n.DS_Store\n")
    write(dest / "CITATION.cff", "cff-version: 1.2.0\nmessage: 'Please cite this research software and the underlying UCI datasets.'\ntitle: 'Weighted Federated Synthetic Data Generation'\ntype: software\nauthors:\n  - family-names: Gupta\n    given-names: Shivansh\nversion: 2026-10-25\n")
    write(dest / "RIGHTS_AND_LICENSING.md", "# Rights and licensing\n\nNo blanket software license is granted for project-owned source pending the owner's explicit choice. The UCI Adult and Bank Marketing datasets are credited in their data manifests as CC BY 4.0; preserve those attributions when reusing data. Third-party Private-PGM, FLAIM and Genuity references are documented by source URL, commit and access protocol in `docs/PUBLISHED_REFERENCE_PROTOCOL.md` and related findings. Their source is not vendored here. The adapted reference scripts are project study code, not a relicense of upstream implementations.\n")
    write(dest / "PROJECT_STATUS.md", "# Project status\n\nThe bounded experimental study is `EXPERIMENTAL_WORK_COMPLETE_WITH_EXPLICIT_SCOPE_LIMITS` as of the 25 October sign-off. Eleven work packages have bounded completed findings; Experiment 3 is an algebraic negative/inapplicable finding. This repository packages their source and saved evidence on 31 October 2026. Packaging does not create new confirmation or an independent-person cohort. See `AUTHOR_READY/FINAL_SIGNOFF.md` and `EXPERIMENTS_01_TO_12_CLOSURE.json`.\n")
    write(dest / "ARTIFACTS.md", "# Artifact status\n\nSee [manifest and access limitations](artifacts/README.md), [complete archived member hashes](artifacts/full_archive_manifest_v2.json) and [source inventory](provenance/source_inventory.json). Original v2 ZIP and immutable freeze remain unchanged. Source, data and small saved result tables are in Git; large checkpoint/synthetic/prediction binaries reside in the verified full archive until a separately verified private release asset is linked.\n")
    write(dest / "REPRODUCIBILITY.md", "# Reproducibility levels\n\n1. `python scripts/audit_repository.py` verifies repository evidence links, hashes, main counts and archived provenance.\n2. `python scripts/reproduce_repository.py --tables` runs the original saved-result report builder. It does not refit or score official test.\n3. `python scripts/reproduce_repository.py --figures` copies the regenerated scientific figures to the gallery.\n4. `python -m pytest -q` runs scientific tests.\n5. Full model/draw replay needs the trusted v2 archive, Python 3.12 pinned environment, and the shared EC2 controller. See `REPRODUCE.md`. Historical 91 tests and clean extraction are not represented as fresh checks unless separately logged under `logs/packaging/`.\n")
    write(dest / "data" / "README_GITHUB.md", "# Dataset provenance\n\nOfficial Adult source archive and originals, and UCI Bank Marketing `bank-additional-full.csv`, are included from the private research project where licensing permits. The preserved `data_manifest.json` files record exact source/member SHA-256 and row counts. Bank `duration` is excluded for the pre-call task. The test files are retained for provenance; reproduction routines must not fit on them. Verify with `python scripts/verify_data_sources.py`.\n")
    write(dest / "results" / "README.md", "# Saved evidence\n\nCanonical small CSV/JSON result files were copied without numeric edits. The source-to-repository hash map identifies each copy. Historical unprojected, corrected development, external Bank, and frozen confirmation outputs remain in separate source directories. Large pickles, generated draws and some per-record files are represented in the full archive manifest and are not silently claimed to be in Git. `results/summaries/` is derived from saved author tables and the original closure register.\n")
    write(dest / "theory" / "README.md", "# Theory index\n\nThe original theoretical framework is preserved in [LaTeX](BTP_Theoretical_Framework.tex) and [PDF](BTP_Theoretical_Framework.pdf). Use [notation](notation.md), [assumptions](assumptions.md), [statement map](statements.md) and [proof-to-experiment map](proof_to_experiment_map.csv) to locate claims. Some formal additions postdate experiment selection; they did not prospectively govern the original protocol. Finite-query bounds are not population-TV guarantees, and numerical identity checks are not proofs.\n")
    theory_dir = ROOT / "docs" / "theory"
    for name in ("BTP_Theoretical_Framework.tex", "BTP_Theoretical_Framework.pdf"):
        src = theory_dir / name
        if src.exists(): shutil.copy2(src, dest / "theory" / name)
    write(dest / "theory" / "notation.md", "# Notation\n\n`D_R` is an observed real reference; `D_S` is generated. `alpha_i=n_i/sum n_j` fixes the declared client-mass target. `w_i` is generator mass. For bounded queries `q_l`, `b_R,l=sum_i alpha_i mean_{D_R,i} q_l`, `b_S,l=mean_{D_S} q_l`, and the measured primary loss is `max_l |b_S,l-b_R,l|`. Unknown population TV is not measured. See the original LaTeX for formal domains.\n")
    write(dest / "theory" / "assumptions.md", "# Assumptions and boundaries\n\nThe same schema holds across clients; client assignment and reference roles are declared. Empirical finite-query bounds need positive condition support and compatible query definitions. Fixed-pilot LP certificates concern only their finite matrix. Projection changes probability masses through preimages. The four FLAIM fits have only a conditional, mechanism-specific approximate-DP interpretation; the main pipeline is nonprivate. See [theory clarifications](../docs/THEORY_CLARIFICATIONS.txt) and [release ledger](../docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md).\n")
    write(dest / "theory" / "post_experiment_additions.md", "# Chronology\n\nThe current report contains later theoretical additions. They are explanatory and future proof targets; they did not control the frozen historical selection. Refer to the original dated report, campaign freeze and `docs/experimental_history.md` when citing prospectivity.\n")
    statements = ["non-IID assignment and mixture targets", "empirical workload loss", "representation bounds", "error decomposition", "convex-hull expressivity", "subset collapse", "identifiability", "model-only information limitation", "finite-pilot oracle inequality", "regularization stability", "pilot and calibration uncertainty", "stratified synthetic sampling", "sufficient fallback certificate", "projection and preimage probabilities", "conditional routing", "conditional transfer", "support and rejection cost", "conditional student filtering", "joint-implied prediction", "bounded-loss transfer", "Brier decomposition", "finite-support pooling", "geometric-score perturbation", "finite entropic-transport bounds", "scoped differential privacy and composition", "exact-model size-weight optimality", "imperfect-model counterexample", "approximate size optimality", "sufficient convex optimality certificate"]
    write(dest / "theory" / "statements.md", "# Statement locator\n\nThe items below locate topics in the preserved [original LaTeX](BTP_Theoretical_Framework.tex); their exact assumptions/proofs must be read there. This index is not a claim that each statement is a novel theorem or prospectively registered.\n\n" + "\n".join(f"- {x}" for x in statements) + "\n")
    with (dest / "theory" / "proof_to_experiment_map.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["topic","proof_location","associated_experiments","empirical_certification","chronology_note"])
        for x in statements:
            w.writerow([x,"theory/BTP_Theoretical_Framework.tex","see twelve-package closure","assumptions not universally certified","some additions postdate selection"])
    write(dest / "paper" / "README.md", "# Writing material\n\nThe empirical writing handoff, LaTeX, typeset PDF, editable tables and scientific figures are in [AUTHOR_READY](../AUTHOR_READY/START_WRITING_HERE.md). The original full report is at [BTP_FINAL_EXPERIMENTAL_REPORT.md](../BTP_FINAL_EXPERIMENTAL_REPORT.md). This is a bounded comparative study, not a publication or acceptance claim.\n")
    write(dest / "figures" / "README.md", "# Scientific figures\n\nCanonical presentation figures and captions are in `../AUTHOR_READY/PAPER_FIGURES/`; saved-result originals are in `../reports/final_build/`. Run `python scripts/reproduce_repository.py --figures` after installing the pinned environment.\n")
    write(dest / "tables" / "README.md", "# Editable tables\n\nCanonical table copies and captions are in `../AUTHOR_READY/PAPER_TABLES/`. Machine-readable result summaries are in `../results/summaries/`. No figure or table contains inferred missing experiment values.\n")
    write(dest / "logs" / "README_GITHUB.md", "# Logs\n\nHistorical research logs remain under `logs/`. Packaging-time tests and integrity commands go under `logs/packaging/` with UTC start/end and exit status. Historical `91 passed` is not a fresh packaging test result.\n")
    history = "# Experimental history\n\nEarly handoff and exploratory/unprojected runs are retained separately from the corrected projected development matrix. The 54 corrected Adult core cells plus three histogram controls, viewed development audits and final validation-only family selection preceded the immutable campaign freeze. Raw official-test source records were read for provenance and duplicate quarantine; first confirmation *scoring* occurred after the freeze, then 12 frozen configurations reused the same test people. Bank replication and later mathematical/editorial additions have separate chronology. This 31 October packaging task does not change any frozen scoring input or create new experiment evidence.\n\nSee `BTP_PROGRESS_REPORT_20261024.md`, `DECISIONS.md`, `docs/TEST_ACCESS_SCOPE_CLARIFICATION.md`, `reports/confirmation/FIRST_OFFICIAL_TEST_READ.json`, `SELECTION_FROZEN.json`, `EXTERNAL_PROTOCOL_FROZEN.json`, and `AUTHOR_READY/FINAL_SIGNOFF.md` for timestamps, hashes and access roles.\n"
    write(dest / "docs" / "experimental_history.md", history)
    write(dest / "README.md", f"""# Weighted Federated Synthetic Data Generation

A reproducible study of representation-constrained aggregation of heterogeneous **non-neural** tabular generators. Each client fits a joint model over the same schema; the statistical server combines released models and permitted summaries to synthesize records. The measured question is whether weighting improves a fixed empirical target over properly tuned size weighting.

## Main answer

The globally selected Adult procedure is a train/local-tune-selected projected Gaussian copula with `w=alpha`, where `alpha_i=n_i/sum n_j` is the declared client-mass target. The constrained challenger has `||w-alpha||_1<=0.25` and `w_i>=0.5 alpha_i`. Its paired primary query-max difference (challenger minus size; negative favours the challenger) was **{summary['adult_development']['mean_paired_delta']:+.9f}** over 18 corrected Adult development slices (0/18 reached the registered -0.005 practical margin), **{summary['confirmation']['overall_constrained_minus_size']:+.9f}** over the frozen Adult official holdout (0/6 slices reached the margin), and **{summary['bank_external']['mean_paired_delta']:+.9f}** in the registered Bank replication (0/4 slices reached it). These are bounded null/adverse findings, not equivalence or a universal impossibility result. See [all slices](AUTHOR_READY/PAPER_TABLES/), [closure](EXPERIMENTS_01_TO_12_CLOSURE.json) and [sign-off](AUTHOR_READY/FINAL_SIGNOFF.md).

The primary empirical reference is `b_R,l=sum_i alpha_i mean_{{z in D_R,i}} q_l(z)`; the synthetic answer is `b_S,l=mean_{{z in D_S}} q_l(z)`. Loss is `max_l |b_S,l-b_R,l|` over 152 registered Adult queries (143 one-way, eight extra two-way, one structural). An additional 23 queries were viewed during development. The official Adult test reused the same people across 12 configurations. `fnlwgt` remains a predictor, not a survey weight.

The frozen conditional teacher satisfied the requested filters, yet the female condition generated `relationship=Husband` at 0.340–0.399 where the alpha-standardized real female conditional reference had zero in the saved cells (mean discrepancy 0.375). The main release is **nonprivate**. Synthetic-trained versus privileged real-trained utility used unequal registered training budgets, which are stated in the tables.

## Project map

- [`btp/`](btp/): original data, models, weighting, projection, sampling, evaluation and privacy code.
- [`scripts/`](scripts/): original cell runners and report/audit tools; repository-specific lightweight wrappers.
- [`configs/`](configs/), [`environment/`](environment/): frozen campaign/resources and pinned Python dependencies.
- [`data/`](data/): official source variants, cleaning/split manifests and checksum provenance.
- [`results/`](results/), [`reports/`](reports/), [`AUTHOR_READY/`](AUTHOR_READY/): inspectable saved evidence, generated tables, captions and writing material.
- [`theory/`](theory/): original LaTeX and interpretation index; proofs and empirical checks remain distinct.
- [`artifacts/`](artifacts/), [`provenance/`](provenance/): full-archive manifest, source mapping and exclusion status.
- [`experiments/`](experiments/): twelve evidence-linked work-package guides.

## Experiment index

""" + "\n".join(f"{i}. [Experiment {i}: {SLUGS[i].replace('_', ' ')}](experiments/exp{i:02d}_{SLUGS[i]}/README.md)" for i in range(1,13)) + """

## Quick start on Linux/Python 3.12

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r environment/requirements_final_portable_20261025.txt
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/verify_data_sources.py
.venv/bin/python scripts/audit_repository.py
.venv/bin/python scripts/reproduce_repository.py --tables
.venv/bin/python scripts/reproduce_repository.py --figures
```

`python -m pytest -q` runs the original scientific test suite. The wrapper only reads saved result files. Full fitting is explicit and governed by [REPRODUCE](REPRODUCE.md) and the shared EC2 resource controller; do not run a campaign just to regenerate figures. The original final-package bootstrap expects the full v2 archive and is not the small Git checkout bootstrap.

## Evidence, data and limits

[Source and artifact status](ARTIFACTS.md) distinguishes files in Git from the verified 537 MB full archive. Model pickles require trusted provenance and are excluded from normal Git history. [Dataset provenance](data/README_GITHUB.md) records official UCI Adult and Bank sources/CC BY 4.0 attribution. [Theory](theory/README.md), [paper material](paper/README.md), [experimental history](docs/experimental_history.md), [release/privacy ledger](docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md), [reproducibility levels](REPRODUCIBILITY.md) and [rights](RIGHTS_AND_LICENSING.md) state what the project proves and does not establish. No whole-pipeline DP, arbitrary-condition fidelity, population-TV measurement, independently recruited cohort, or novel weighting-algorithm superiority is claimed. The 12 packages close at their registered bounded scope.

Please cite the research software using [CITATION.cff](CITATION.cff) and cite the original UCI datasets as recorded in their manifests.
""")


if __name__ == "__main__":
    main()
