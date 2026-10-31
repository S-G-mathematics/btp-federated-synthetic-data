# Editable paper tables

`TABLE_CAPTIONS.csv` records each table's source path, data role and unit convention. Rows are copied from immutable saved reports unless their caption says they are a deterministic join of saved tables. Use the exact metric named in a column; do not treat a Brier score, AUROC, count, byte total and empirical query proportion as interchangeable units.

## Primary comparisons

- `adult_development_slices.csv`: corrected projected Adult development, three-seed generator/partition/K slices. The comparison column is constrained minus size empirical query-max; negative favours constrained. Eighteen core slices, no practical gain at -0.005. These share Adult people.
- `adult_confirmation_all_draws.csv` and `adult_confirmation_slices.csv`: frozen official Adult test, 12 cells × three methods × five draws. The slice file averages seeds within partition/K; six slices. The same 16,281 official people recur across all cells.
- `bank_external_slices.csv` and `bank_external_paired_cells.csv`: prospectively frozen external Bank assessment, 12 cells and four generator/partition slices. Contacts may repeat.

## Mechanisms and secondary endpoints

- `pilot_size_*.csv` concerns finite synthetic matrices and fixed model checkpoints. An LP certificate is a finite-matrix optimum, not a population oracle.
- `synthetic_size_*.csv` uses 2,500, 10,000 and 40,000 generated rows from six fixed checkpoints, five draws at each size. Draw variation is conditional on the models.
- `conditional_*.csv` records trained-student/direct-teacher development outcomes and frozen direct-teacher support. `female_dependency_worst_query.csv` was assembled from all 12 saved confirmation `conditional_per_query.csv` files without resampling; proportions are within the female condition.
- `utility_with_registered_budgets.csv` joins frozen utility outcomes to checked per-cell training/tune/calibration counts. Real TRTR has privileged real-data access and more training rows than synthetic TSTR; do not call this a matched-size study.
- `joint_implied_*.csv`, `query_*.csv`, `projection_mechanism.csv`, `summary_access_ablation.csv`, `severity_*.csv` and `conditional_transfer_*.csv` are developmental or mechanism tables. The observed support and finite-query assumptions are part of each interpretation.
- `private_pgm_cell_means.csv`, `flaim_cell_means.csv` and `published_reference_access.csv` are descriptive published-code references with different privacy/access contracts. The FLAIM composition tuple is conditional and does not cover the main pipeline.
- `raw_vs_model_payload_*.csv` uses matched pickle5+gzip6 application payload bytes; it is not WAN or TLS traffic.

The complete per-query, prediction, pilot and failure records remain in the immutable full project archive cited in `../START_WRITING_HERE.md`. These editable paper tables are a reading and drafting subset, not a replacement for the full evidence package.
