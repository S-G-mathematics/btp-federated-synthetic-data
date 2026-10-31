# Reproduce the bounded BTP evidence

The authoritative project is the private final ZIP, with the SHA-256 shown in the delivery receipt. Use a fresh extraction on the verified EC2 with Python 3.12, one BTP compute lane and the existing shared lease. The official UCI Adult and Bank source archives, member hashes, cleaning manifests and attribution are in `data/`, `data/external_bank/` and `docs/DATA_PROTOCOL.md`. Do not substitute a Kaggle Adult copy or the older Bank `bank-full.csv`. Checkpoints are trusted research pickles; never load pickles from an untrusted source.

## Fresh extraction and pinned environment

The final archive extracts `btp_ec2_handoff/` plus `ORIGINAL_HANDOFF/`. Create a **new empty** destination; do not overwrite the active research project. From the extracted `btp_ec2_handoff` directory:

```bash
python3 scripts/verify_delivered_archive.py --archive /home/ubuntu/research-director/btp-federated-statistics-20261024/BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip
bash scripts/bootstrap_final_package.sh
```

The verifier hashes **every ZIP member** against the embedded final manifest, checks the preserved original handoff ZIP, and rejects missing, extra, duplicate or unsafe paths. The bootstrap refuses to overwrite an existing `.venv`, creates an isolated Python 3.12 environment from `environment/requirements_final_portable_20261025.txt`, installs this extracted package locally, runs the 91-test suite, checks the campaign freeze against its frozen scoring inputs, and regenerates one confirmation draw byte-for-byte. The recorded `environment/requirements_confirmation_20261025.txt` contains the original EC2 absolute editable-install path and is a provenance record, **not** a portable install command. The old `scripts/bootstrap_ec2.sh` and `scripts/verify_bundle.py` validate the **original immutable handoff**; their original-bundle hash check correctly rejects this edited final project.

The main project remains nonprivate. A separate FLAIM reference used Python 3.9 and a pinned author checkout with a recorded compatibility patch; see `docs/PUBLISHED_REFERENCE_FINDINGS.md`. Its environment is distinct from the BTP package.

## Rebuild tables from saved evidence, without refitting

In an already bootstrapped extraction, these commands read saved artifacts. They do not select a new method or retrain the official confirmation:

```bash
.venv/bin/python scripts/audit_completion_integrity.py
.venv/bin/python scripts/build_final_reports.py --build
.venv/bin/python scripts/index_all_runs.py
.venv/bin/python scripts/verify_final_package.py
```

The integrity audit reconstructs the corrected Adult cell counts, LP certificates, fixed target and projected-score preimage check. The report builder outputs `reports/final_build/summary.json`, CSVs and PNGs from saved results. `scripts/verify_final_package.py` checks twelve primary and twelve secondary confirmation cells, frozen hashes, saved synthetic draw hashes, and the reproduced named query maximum. For the data source/split audit, run `.venv/bin/python scripts/validate_data.py`; that command reads official-test source records for provenance and train/test duplicate quarantine but **does not score the official test or select methods**. The original first confirmation-scoring audit is `reports/confirmation/FIRST_OFFICIAL_TEST_READ.json`; its precise meaning is explained in `docs/TEST_ACCESS_SCOPE_CLARIFICATION.md`.

The current 91-test and freeze-gate rerun is recorded at `logs/final_goal_continuation_tests_20261025.log` and `logs/final_goal_continuation_freeze_gate_20261025.log`. Historical failed attempts and corrected lineage are in `ALL_FAILURES_AND_REPAIRS.md`. The final archive verifier log and clean-extraction log document the portable package check.

## Frozen roles and evidence map

`SELECTION_FROZEN.json` is the complete official Adult procedure, canonical SHA-256 `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. The selected procedure is projected copula with exact size weights. The official confirmation already used the fixed seeds 404/505 and official people; running it again would be a repeat on the **same holdout**, not an independent confirmation. Scoring entry points `scripts/run_adult_confirmation.py` and `scripts/report_adult_confirmation_secondary.py` are freeze-hashed and must not be edited to improve an observed result. The earlier generic starter `--official-test` route is disabled.

- Corrected Adult development: `results/ec2_projected_v2_deterministic_20261024/`, `results/representation_constrained_projected_v2_deterministic_20261024/`, `reports/completion_integrity_20261025/`.
- Global validation choice: `reports/completion_selection_20261025/`, `docs/GLOBAL_SELECTION_DECISION.md`.
- Frozen Bank protocol and 12 cells: `EXTERNAL_PROTOCOL_FROZEN.json`, `data/external_bank/`, `results/external_bank_20261025/`, `reports/external_replication/`.
- Mechanism cells: `reports/mechanisms/`, `docs/EXP09_ABLATION_CLOSURE.md`, `docs/EXP10_MECHANISM_CLOSURE.md`.
- Published code references: `reports/published_references/`, `docs/PUBLISHED_REFERENCE_FINDINGS.md`.
- Frozen official Adult: `results/adult_confirmation_20261025/`, `reports/final_build/confirmation_*.csv`, `docs/FROZEN_CONFIRMATION_FINDINGS.md`.
- Access/privacy/resources: `docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md`, `reports/resources/`.
- Historical/current run categories and failures: `ALL_RUNS_INDEX.csv/json`, `ALL_FAILURES_AND_REPAIRS.md`; complete claim-to-artifact mapping: `docs/EVIDENCE_INDEX.md` and `EXPERIMENTS_01_TO_12_CLOSURE.json`.

Any new heavy computation requires checking the actual controller, at least 8 GiB available RAM and 5 GiB free disk, using `~/research-director/control/heavy-compute.lock`, one worker and one native thread, and respecting the registered worker-hour/campaign limits. No new computation is required to rebuild the delivered report.
