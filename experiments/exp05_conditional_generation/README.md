# Experiment 05: Conditional generation

**Research question.** For registered conditions, how do direct rejection and separately trained conditional students compare, and when must they abstain?

**Setup and stage.** Development used six fixed Chow-Liu age/K5 and mixed-GMM label-skew/K10 cells, seeds 101/202/303, under size and constrained weights. Separate 30,000-row teacher pools trained per-condition students and supplied direct rejection; accepted-row counts were matched up to 2,000. Frozen confirmation is reported separately.

**Observed result.** In development, direct rejection had lower mean maximum feature-query error for the age and age-plus-education conditions in each family/weight mean; the rare older-doctorate condition abstained in all 12 routes. In confirmation, the female-condition relationship=Husband query was worst in 12/12 cells: real frequency zero, generated 0.340–0.399, mean error 0.375, despite zero condition violations.

**Limits.** Support and condition compliance do not certify fidelity. Students were trained per condition; arbitrary requests and cross-condition generalization were not tested.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/PROJECTED_CONDITIONAL_FINDINGS_20261024.md](../../docs/PROJECTED_CONDITIONAL_FINDINGS_20261024.md)
- [docs/FROZEN_CONFIRMATION_FINDINGS.md](../../docs/FROZEN_CONFIRMATION_FINDINGS.md)
- [reports/final_build/confirmation_conditional.csv](../../reports/final_build/confirmation_conditional.csv)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
