# Experiment 09: Controlled ablations

**Research question.** What changes under isolated projection and released-summary access variants?

**Setup and stage.** Development-only checkpoint audits used 12 structural projection cells and six summary-access cells, with no refitting. Projection applied the public education-number mapping to the same raw rows. The access comparison restricted the same fixed pilot and calibration summary to 143, 151 or 152 queries.

**Observed result.** Projection reduced the primary maximum from about 0.268–0.328 to 0.028–0.033 for Chow-Liu and 0.693–0.708 to 0.049–0.055 for GMM; relation violations became zero. The 151- and 152-query solutions and losses matched in all six access cells.

**Limits.** The primary workload includes the repaired relation; projection need not improve every statistic. Access variants release different information and do not establish a general weighting gain.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/EXP09_ABLATION_CLOSURE.md](../../docs/EXP09_ABLATION_CLOSURE.md)
- [reports/mechanisms](../../reports/mechanisms)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
