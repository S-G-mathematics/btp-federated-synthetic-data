# Experiment 11: Conditional transfer

**Research question.** What finite-query conditional bound and teacher/student accounting hold under measured support?

**Setup and stage.** Six development cells used Chow-Liu age/K5 and mixed GMM label-skew/K10, seeds 101/202/303, two weight routes and four registered conditions. The audit evaluated 142 feature-only queries; student/direct comparisons were made only for supported combinations.

**Observed result.** The finite-query ratio bound held in all 48 condition/route/cell rows, and the empirical triangle held in all 5,112 supported student/direct query rows. The rare condition failed the prior 300-row/1% teacher gate in every route and abstained.

**Limits.** The bound requires measured joint intersections and positive condition mass; rare support makes it weak. Finite empirical checks do not prove arbitrary-condition or population transfer.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md](../../docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md)
- [docs/PROJECTED_TRANSFER_FINDINGS_20261025.md](../../docs/PROJECTED_TRANSFER_FINDINGS_20261025.md)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
