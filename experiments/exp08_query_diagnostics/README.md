# Experiment 08: Query diagnostics

**Research question.** Which finite-workload queries dominate the observed maximum error?

**Setup and stage.** The audit examines saved projected development draws and frozen Adult confirmation draws, recording query identity, support, arity and error. The targeted development audit contains 10,500 answers across 175 queries; 23 additional audit queries were viewed during development. The primary metric is the maximum absolute error over the registered workload.

**Observed result.** In confirmation, the size-weighted primary mean was 0.022216; the HS-grad/high-income query was dominant in 33/60 size draws.

**Limits.** These are empirical finite-workload diagnostics. They do not establish arbitrary-query accuracy or population total variation; development audit queries were viewed during design.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md](../../docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md)
- [reports/final_build/confirmation_dominant_queries.csv](../../reports/final_build/confirmation_dominant_queries.csv)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
