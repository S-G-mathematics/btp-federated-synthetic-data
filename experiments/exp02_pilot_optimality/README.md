# Experiment 02: Pilot optimality

**Research question.** How sensitive is the finite-pilot constrained solution to pilot size, and does a larger pilot yield practical fresh-sample gains?

**Setup and stage.** Six fixed development cells: Chow-Liu age/K5 and mixed GMM label-skew/K10, seeds 101/202/303. Pilot sizes 500, 1,500, 5,000 and 15,000 rows/client had five pilot seeds each; a disjoint 30,000-row/client synthetic H_ref and one fresh 10,000-row assessment draw per fit were used. All constrained LP certificates succeeded.

**Observed result.** Mean same-target finite-H_ref LP excess fell below 0.001 at 15,000 for both families. No pilot size achieved the registered -0.005 three-seed mean improvement on fresh assessment.

**Limits.** The oracle is conditional on a finite synthetic matrix and empirical calibration target, not a population or nonlinear pooling optimum. Models and Adult people are shared across replicates.

**Reproduction.** `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. For historical execution, prerequisites, and selecting a specific cell, see [REPRODUCE](../../REPRODUCE.md), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt), [source](../../btp/) and [runners](../../scripts/).

**Evidence.**
- [docs/PROJECTED_PILOT_SENSITIVITY_FINDINGS_20261024.md](../../docs/PROJECTED_PILOT_SENSITIVITY_FINDINGS_20261024.md)
- [reports/projected_pilot_sensitivity_v2_20261024](../../reports/projected_pilot_sensitivity_v2_20261024)

See the [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md), [freeze](../../SELECTION_FROZEN.json), [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
