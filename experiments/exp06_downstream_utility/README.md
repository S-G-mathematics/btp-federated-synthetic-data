# Experiment 06: Downstream utility

**Research question.** How well do synthetic-trained income predictors perform on held-out real data?

**Setup and stage.** Frozen Adult confirmation compares synthetic-trained logistic regression and extra trees with privileged real-trained TRTR on held-out real data. The logistic comparison uses 10,000/2,000/2,000 generated train/tune/calibration rows versus 21,148/4,880/3,254 real rows for TRTR.

**Observed result.** Size-weighted synthetic logistic Brier was 0.129818 versus 0.101987 for TRTR; AUROC was 0.856167 versus 0.904646. Lower Brier and higher AUROC are better.

**Limits.** The budgets differ, so this is not a matched-size causal comparison. Small subgroup coverage and overlapping split seeds limit inference.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/FROZEN_CONFIRMATION_FINDINGS.md](../../docs/FROZEN_CONFIRMATION_FINDINGS.md)
- [reports/final_build/confirmation_utility.csv](../../reports/final_build/confirmation_utility.csv)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
