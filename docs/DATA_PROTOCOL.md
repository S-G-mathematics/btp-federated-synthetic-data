# UCI Adult data protocol

`btp.data.read_adult(raw_dir)` reads the official `adult.data` and `adult.test`
files and returns the 15 source columns in their original order. The index is a
stable `row_id` (`train:000000` or `test:000000`); it is metadata and must never
be passed to a model as a predictor. The expected official row count is 32,561
training rows plus 16,281 official test rows. All six numeric predictors are
parsed as numbers. The eight categorical predictors are stripped of surrounding
whitespace. A source `?` remains an explicit missing category, and no rows are
dropped. The trailing period in official test labels is removed so both files
use exactly `<=50K` and `>50K`.

`prepare_splits(raw_dir, seed=42)` reserves the official test file as the locked
test set. It identifies exact duplicate records using all 15 values, and
quarantines every official-training row whose full record occurs in official
test. Thus test has no exact full-record duplicates in development data. Among
remaining official-training rows, it groups identical records first and
stratifies those groups by income into train/tune/calibration/validation at
65/15/10/10. All rows from a duplicate group stay in one split. It returns those
five splits plus `quarantine`, retaining original row IDs throughout. Each
returned frame has the same `attrs["manifest"]` with row counts, seed, and policy.
For a reproducible seed sweep, call this function for each predeclared seed;
never use test labels to adjust split sizes or client assignments.

To create non-IID clients, fit one rule with
`build_partition_rule(splits["train"], k, kind, seed, severity)`, then use
`rule.assign(frame)` for every split, including test. Rules support `age`,
`age_education` (age and education-num), and `label_skew`. Feature cut points
and label-to-client probabilities are estimated/generated once from training
data only and then fixed. Assignment randomness is keyed by stable row IDs, so
it is reproducible and independent of frame order. Do not fit a separate rule
on any evaluation split. Client assignments are returned as integer IDs in
`[0, k)`; downstream code should report client sizes and handle empty or tiny
clients explicitly. Global metrics should use the original row-level target
population (for example, an alpha-weighted aggregation if training allocates
unequal client mass), rather than an unweighted mean over client metrics.
# Label-skew assignment floor (handoff update)

The label-skew rule uses a fixed, predeclared mixture `0.95 * Dirichlet_draw + 0.05 / K` for each label. This supplies 5% common assignment mass before any held-out records are assigned. It is an allocation design choice, not a post-hoc repair based on validation/test counts; report its actual achieved skew. All other assignment rules and split isolation are unchanged.

