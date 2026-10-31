# Twelve experimental work packages

These twelve packages cover empirical comparisons, mathematical checks and audits; they are not twelve independent training campaigns. Each guide identifies its question, bounded setup, result, limits and retained evidence. Development findings are historical and exploratory; the frozen Adult confirmation used the official test only after selection was frozen. Bank is a separate registered external replication.

The primary fixed-target result is a practical null: constrained weighting met the 0.005 improvement margin in 0/18 Adult development generator/partition/K slices (overall delta +0.002428), 0/6 Adult confirmation partition/K slices (−0.000214907), and 0/4 Bank replication generator/partition slices at K=5 (−0.001331749). Deltas are constrained minus size, so negative favors constrained weighting. This does not establish equivalence.

From the repository root, `python scripts/reproduce_repository.py --tables` rebuilds reports from saved results without fitting. See [REPRODUCE](../REPRODUCE.md) for prerequisites and explicitly selected historical runs.

- [exp01 fixed target weighting](exp01_fixed_target_weighting/README.md)
- [exp02 pilot optimality](exp02_pilot_optimality/README.md)
- [exp03 subset composition](exp03_subset_composition/README.md)
- [exp04 synthetic sample size](exp04_synthetic_sample_size/README.md)
- [exp05 conditional generation](exp05_conditional_generation/README.md)
- [exp06 downstream utility](exp06_downstream_utility/README.md)
- [exp07 joint implied prediction](exp07_joint_implied_prediction/README.md)
- [exp08 query diagnostics](exp08_query_diagnostics/README.md)
- [exp09 controlled ablations](exp09_controlled_ablations/README.md)
- [exp10 heterogeneity](exp10_heterogeneity/README.md)
- [exp11 conditional transfer](exp11_conditional_transfer/README.md)
- [exp12 privacy and resources](exp12_privacy_and_resources/README.md)

[Statistical synthesis](../docs/RESULTS_AND_STATISTICAL_INFERENCE.md) · [Acceptance table](../AUTHOR_READY/TWELVE_PACKAGE_ACCEPTANCE.md)

