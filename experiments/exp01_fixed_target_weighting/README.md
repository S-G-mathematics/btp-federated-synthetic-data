# Experiment 01: Fixed target weighting

**Research question.** Can constrained client weights improve fixed-alpha query fidelity over size weights by the registered practical margin?

**Setup and stage.** The corrected Adult development core crossed three generators (copula, Chow-Liu and mixed GMM), three partitions (age, age+education and label skew), K=5/10 and seeds 101/202/303: 54 matched fitting cells. Three independent-histogram controls are separate. Across 57 source cells there are 57 successful fixed-pilot LP records, 741 method rows and 3,705 method/cell/draw assessment rows. Frozen confirmation used the selected copula and seeds 404/505. The selected projected copula and weights were frozen before official-test scoring. The constrained rule uses an L1 budget of 0.25 and floor of 0.5 alpha; the primary metric is alpha-standardized Q_primary_v2 query maximum, with five m=10,000 draws. Bank is a separate registered external replication: copula and Chow-Liu, age+education and label-skew partitions, K=5, seeds 611/622/633, with duration excluded.

**Observed result.** At the 0.005 practical improvement margin, Adult development reached it in 0/18 generator/partition/K slices (overall constrained-minus-size delta +0.002428); frozen Adult confirmation reached it in 0/6 partition/K slices (delta -0.000214907); Bank replication reached it in 0/4 generator/partition slices at K=5 (delta -0.001331749). Each cell averages five draws; development and Bank slices average three seeds, confirmation slices two. Negative differences favor constrained weights. Size weighting remains the fixed-target fallback.

**Limits.** This is a failure to establish the registered practical gain, not proof of equivalence or a universal weighting result. Split seeds reuse people; Bank is one external dataset.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/ADULT_WEIGHTING_DEVELOPMENT_CLOSURE.md](../../docs/ADULT_WEIGHTING_DEVELOPMENT_CLOSURE.md)
- [docs/FROZEN_CONFIRMATION_FINDINGS.md](../../docs/FROZEN_CONFIRMATION_FINDINGS.md)
- [reports/final_build/confirmation_slices.csv](../../reports/final_build/confirmation_slices.csv)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
