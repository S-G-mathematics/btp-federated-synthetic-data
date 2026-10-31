# Experiment 04: Synthetic sample size

**Research question.** How do query error and draw variation change as synthetic sample size increases?

**Setup and stage.** Six fixed development cells: Chow-Liu age/K5 and mixed GMM label-skew/K10, seeds 101/202/303, with fixed size and constrained weights. Five draws per method/cell were assessed at m=2,500, 10,000 and 40,000; the compatible 10,000-row draws were reused.

**Observed result.** The size-weighted five-draw range fell about 73% and 78% respectively from 2,500 to 40,000; mean query error persisted. Neither family met the -0.005 practical margin at any tested size.

**Limits.** These are finite development assessments for two selected families, not a population error floor; streams and split seeds are not independent cohorts.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/PROJECTED_SAMPLE_SIZE_FINDINGS_20261024.md](../../docs/PROJECTED_SAMPLE_SIZE_FINDINGS_20261024.md)
- [reports/projected_sample_size_20261024](../../reports/projected_sample_size_20261024)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
