# What the saved results establish

This synthesis is a post-experiment descriptive analysis of saved cell means. It does not change selection, score new people, or rerun generators. Each cell averages its registered synthetic draws. Negative challenger-minus-size differences favour constrained weighting.

| Evidence stage | Cells | Size loss | Challenger loss | Mean difference | Median difference | Improved cells | Gain ≥0.005 cells |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| adult_confirmation | 12 | 0.022216 | 0.022001 | -0.000215 | -0.000198 | 7 | 0 |
| adult_development | 54 | 0.035633 | 0.038061 | +0.002428 | +0.000536 | 24 | 3 |
| bank_external | 12 | 0.048121 | 0.046789 | -0.001332 | -0.001079 | 9 | 1 |

Cell win counts above are descriptive, and are distinct from the registered practical-gain decision on seed-averaged slices. The registered slice counts remain 0/18 Adult development, 0/6 Adult official holdout, and 0/4 Bank external. A favourable individual cell does not establish a qualifying slice or global method.

## Generator dependence

| Stage | Generator | Cells | Mean difference | Median difference | Observed range |
| --- | --- | ---: | ---: | ---: | --- |
| adult_confirmation | copula | 12 | -0.000215 | -0.000198 | [-0.001162, +0.001200] |
| adult_development | chow_liu | 18 | +0.001296 | +0.000096 | [-0.003120, +0.009712] |
| adult_development | copula | 18 | +0.001976 | +0.000536 | [-0.002643, +0.015434] |
| adult_development | mixed_gmm | 18 | +0.004012 | +0.004191 | [-0.006546, +0.019260] |
| bank_external | chow_liu | 6 | -0.002277 | -0.001643 | [-0.007280, +0.001573] |
| bank_external | copula | 6 | -0.000386 | -0.000318 | [-0.002380, +0.001522] |

## Statistical interpretation

- Means summarize the fixed registered design with equal weight per cell. They do not estimate performance across a random population of federated tasks.
- Medians, quartiles and observed ranges reveal heterogeneity. Ranges are not confidence intervals. The ratio of mean losses in the CSV is descriptive and differs from averaging cell-relative changes.
- Adult cells reuse people, partitions and model families. Synthetic draws share checkpoints. Bank contacts may share individuals. No p-value or narrow independent-cell confidence interval is justified by treating these records as independent cohorts.
- The registered 0.005 margin is operational. Failure to reach it does not establish equivalence, zero benefit, or universal optimality of size weights.
- No omnibus mean combines development, official holdout and Bank. They have different roles and workloads. Viewed development diagnostics remain exploratory.

## Mechanisms and adverse results

The female conditional has a measured sex/relationship dependency failure: mean feature-query maximum 0.375, with relationship=Husband the worst query in all twelve confirmation cells. Requested-condition compliance does not validate other features. Rare-condition abstentions and poor conditional students remain in the evidence.

Logistic TSTR Brier 0.129818 versus privileged TRTR 0.101987 is a registered-budget comparison. Real train/tune/calibration sizes are 21,148/4,880/3,254; synthetic sizes are 10,000/2,000/2,000. These results cannot establish an intrinsic difference at matched sample sizes.

Finite-pilot LP certificates apply to their saved matrices and targets. Schema projection, local-model quality, summary access and target-mass constraints explain different parts of the observed behavior; historical changes that alter several parts together are not isolated causal ablations.

The main pipeline remains nonprivate. Conditional histogram and adapted FLAIM accounting apply only to their declared releases and assumptions. Model/raw application payload ratios of 1.915–2.866 do not support a compression claim or a WAN traffic estimate.

## Inspect and reproduce

- [All paired cells](../reports/statistical_synthesis/paired_cells.csv)
- [Every slice and its range](../reports/statistical_synthesis/slice_summary.csv)
- [Generator summaries](../reports/statistical_synthesis/generator_summary.csv)
- [Input hashes and analysis scope](../reports/statistical_synthesis/provenance.json)
- [Conditional evidence](../AUTHOR_READY/PAPER_TABLES/female_dependency_worst_query.csv)
- [Utility budgets](../AUTHOR_READY/PAPER_TABLES/utility_with_registered_budgets.csv)
- [Twelve-package acceptance](../AUTHOR_READY/TWELVE_PACKAGE_ACCEPTANCE.md)

Run `python scripts/build_statistical_synthesis.py`. Only saved CSV files are read.
