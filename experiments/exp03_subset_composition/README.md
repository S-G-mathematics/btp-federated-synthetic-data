# Experiment 03: Subset composition

**Research question.** Does regrouping fixed client distributions into overlapping subsets expand the family of mixtures?

**Setup and stage.** This is an algebraic identity, supported by a saved numerical subset check; it does not fit a new generator. Each subset is itself a mixture of the same client distributions.

**Observed result.** A mixture of subset mixtures collapses to a single mixture with effective client masses; regrouping alone adds no expressive family.

**Limits.** The identity does not cover new estimators trained within subsets or other changes to the client distributions.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/EXPERIMENTS_12.md](../../docs/EXPERIMENTS_12.md)
- [docs/WEIGHT_METHODS.md](../../docs/WEIGHT_METHODS.md)
- [results/ec2_fullstage_dev_20261024/copula_age_k5_s101_24ff1a5a4b33acfa/exp03_subsets.json](../../results/ec2_fullstage_dev_20261024/copula_age_k5_s101_24ff1a5a4b33acfa/exp03_subsets.json)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
