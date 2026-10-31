# Experiment 12: Privacy and resources

**Research question.** What privacy and resource claims are supported for the released pipeline and reference baselines?

**Setup and stage.** The audit separates the nonprivate main pipeline, conditional private atom histogram, nonprivate PGM and adapted FLAIM reference, and measures serialized release payloads against matched raw bytes.

**Observed result.** The main pipeline is nonprivate. Model plus metadata measured 1.915–2.866 times matched raw bytes. The conditional histogram ledger gives epsilon 13 if three settings are released under its stated accounting assumptions.

**Limits.** The conditional reference is not a whole-pipeline DP guarantee; FLAIM is not a privacy-matched ranking, and payload bytes do not measure WAN transfer or security.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md](../../docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md)
- [reports/resources](../../reports/resources)
- [docs/PUBLISHED_REFERENCE_FINDINGS.md](../../docs/PUBLISHED_REFERENCE_FINDINGS.md)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
