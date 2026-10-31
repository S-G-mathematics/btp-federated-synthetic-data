# Experiment 07: Joint-implied prediction

**Research question.** Can the fitted joint mixture imply useful income predictions on observed feature rows?

**Setup and stage.** Six development cells: Chow-Liu age/K5 and mixed GMM label-skew/K10 at seeds 101/202/303. Both income labels were scored and normalized on the same assessment people as the synthetic logistic and privileged TRTR comparisons, under size and constrained weights.

**Observed result.** Two-label mass was finite for every observed assessment row. Size-weighted Chow-Liu joint Brier was 0.128481 versus 0.137953 for synthetic logistic; GMM joint Brier was 0.126214 versus 0.116265.

**Limits.** Chow-Liu scores are exact for its declared discretized fitted model; GMM rounded/clipped output scores are approximate. Observed-row coverage does not imply off-support coverage.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/INTEGRITY_AND_PROJECTION_AUDIT.md](../../docs/INTEGRITY_AND_PROJECTION_AUDIT.md)
- [docs/PROJECTED_JOINT_PREDICTION_FINDINGS_20261025.md](../../docs/PROJECTED_JOINT_PREDICTION_FINDINGS_20261025.md)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
