# Experiment 10: Heterogeneity

**Research question.** Does increasing achieved partition severity change the benefit of constrained weighting at fixed client quantities?

**Setup and stage.** Six newly fitted Adult development copula cells fixed K=5, equal target mass and 1,000 train/200 tune rows per client. Seeds 711/722/733 crossed severity mixtures 0.25 and 0.85; each cell used five m=10,000 draws.

**Observed result.** Client mean-age ranges increased from about 5.1–5.8 to 21.3–21.8 years. Mean size versus constrained query maxima were 0.034804 versus 0.033317 at low severity and 0.034918 versus 0.033541 at high severity. Neither gain met 0.005, and seed-level severity contrasts changed sign.

**Limits.** This manipulation does not isolate every assignment or conditional-distribution effect; three split seeds reuse Adult people. It is not a population-TV decomposition.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/EXP10_MECHANISM_CLOSURE.md](../../docs/EXP10_MECHANISM_CLOSURE.md)
- [reports/mechanisms](../../reports/mechanisms)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
