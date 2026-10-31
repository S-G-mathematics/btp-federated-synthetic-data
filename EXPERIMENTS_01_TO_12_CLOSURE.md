# Experiments 1–12: bounded scientific closure

**Overall:** experimental work complete with explicit scope limits. A bounded negative or inapplicable result is a closed question; it is not a claim that every conceivable experiment was performed.

The primary target is the alpha-standardized empirical client reference, and size weighting fixes `w=alpha`. The official Adult test was opened only after the campaign freeze. The main pipeline is nonprivate. Exact paths below resolve within this archive.

## Experiment 1: Does weighting improve fixed-target empirical fidelity?

- **Methods:** 54 corrected Adult development cells; 12 frozen confirmation cells; same locally tuned models and five 10k draws.
- **Metric:** alpha-standardized Q_primary_v2 query max; constrained minus size.
- **Completed finding:** 0/18 Adult development and 0/6 confirmation partition/K slices reached -0.005; overall confirmation delta -0.000215.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. No registered practical constrained gain; retain size weighting.
- **Stop criterion:** All registered Adult development and frozen confirmation cells terminal; compare the same alpha target and retain every adverse slice.
- **Unresolved wider scope:** Other populations, workloads and privacy-matched aggregation.
- **Forbidden claim:** A general weighting-improvement or equivalence claim.
- **Evidence:** `docs/ADULT_WEIGHTING_DEVELOPMENT_CLOSURE.md`, `docs/FROZEN_CONFIRMATION_FINDINGS.md`, `reports/final_build/confirmation_slices.csv`.

## Experiment 2: How close are candidates to a finite-pilot oracle?

- **Methods:** 57 certified fixed-pilot LPs; six-cell four-size/five-seed pilot sensitivity.
- **Metric:** LP certificate, pilot regret and fresh-sample query loss.
- **Completed finding:** Finite matrix optimum certified; larger pilots reduced numerical excess but did not establish practical fresh-sample gain.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Oracle is conditional on fixed synthetic H and empirical target.
- **Stop criterion:** Every finite-pilot LP status/certificate retained and the predeclared pilot-size study terminal; do not claim a population optimum.
- **Unresolved wider scope:** Population optimum or globally optimal nonlinear operators.
- **Forbidden claim:** Population or continuous-pooling optimality.
- **Evidence:** `docs/PROJECTED_PILOT_SENSITIVITY_FINDINGS_20261024.md`, `reports/projected_pilot_sensitivity_v2_20261024/`.

## Experiment 3: Do overlapping client subsets add mixture expressivity?

- **Methods:** Cyclic subset effective-weight identity and saved numerical check.
- **Metric:** Equality of effective client mass and resulting mixture.
- **Completed finding:** Mixtures of subset mixtures collapse to one global mixture.
- **Disposition:** `CLOSED_NEGATIVE_OR_INAPPLICABLE`. Subset regrouping alone adds no expressive family.
- **Stop criterion:** Algebraic collapse proved and a saved cyclic example has zero effective-weight identity error; no extra expressive model claimed.
- **Unresolved wider scope:** New within-subset estimators.
- **Forbidden claim:** Novel subset generator from regrouping.
- **Evidence:** `docs/EXPERIMENTS_12.md`, `docs/WEIGHT_METHODS.md`, `results/ec2_fullstage_dev_20261024/copula_age_k5_s101_24ff1a5a4b33acfa/exp03_subsets.json`.

## Experiment 4: What changes with synthetic sample size?

- **Methods:** Six checkpoints, m=2500/10000/40000, five draws each.
- **Metric:** query error, draw variation, diversity, runtime.
- **Completed finding:** Draw variation shrank; model error persisted; no practical constrained gain.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Sampling more rows does not repair observed model bias in these cells.
- **Stop criterion:** Five draws at each registered m share fixed checkpoints; separate draw variation from model-error plateau and retain diversity/runtime.
- **Unresolved wider scope:** Other families or very large m.
- **Forbidden claim:** Universal population error floor.
- **Evidence:** `docs/PROJECTED_SAMPLE_SIZE_FINDINGS_20261024.md`, `reports/projected_sample_size_20261024/`.

## Experiment 5: When does conditional synthesis succeed or abstain?

- **Methods:** Six development student/direct-teacher cells; frozen 12-cell four-condition confirmation.
- **Metric:** support, acceptance, violations, within-condition query max.
- **Completed finding:** Direct teacher default; rare request abstained 12/12. Female-condition `relationship=Husband` was the worst feature query in all 12 confirmation cells: real reference frequency zero, generated 0.340–0.399, mean error 0.375 despite zero condition violations.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Support-gated rejection is operationally valid for registered requests; fidelity still limited.
- **Stop criterion:** Registered teacher/student comparison and off-seed support audit terminal; accepted rows satisfy requests, low-support requests abstain, and within-condition errors remain visible.
- **Unresolved wider scope:** Arbitrary-condition fidelity certification or learned cross-condition generalization.
- **Forbidden claim:** Universal conditional accuracy.
- **Evidence:** `docs/PROJECTED_CONDITIONAL_FINDINGS_20261024.md`, `docs/FROZEN_CONFIRMATION_FINDINGS.md`, `reports/final_build/confirmation_conditional.csv`.

## Experiment 6: Does synthetic training preserve income probability utility?

- **Methods:** Paired logistic/extra-trees, synthetic TSTR and privileged real TRTR, six development and 12 confirmation cells.
- **Metric:** Brier, AUROC, AUPRC, log loss, subgroup coverage.
- **Completed finding:** At registered unequal budgets, confirmation size logistic Brier 0.129818 versus TRTR 0.101987; size AUROC 0.856167 versus 0.904646. TRTR used 21,148/4,880/3,254 real train/tune/calibration rows versus 10,000/2,000/2,000 synthetic rows.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Real-trained reference outperformed synthetic-trained predictors at this scope.
- **Stop criterion:** Same-person TSTR/TRTR proper scores, calibration and supported client/subgroup counts retained; no test-derived tuning or synthetic-over-real claim.
- **Unresolved wider scope:** Independent cohort utility and small unsupported subgroups.
- **Forbidden claim:** Synthetic-over-real superiority.
- **Evidence:** `docs/FROZEN_CONFIRMATION_FINDINGS.md`, `reports/final_build/confirmation_utility.csv`.

## Experiment 7: Can a joint model imply an income predictor?

- **Methods:** Six same-person projected development comparisons; exact finite Chow-Liu route and approximate GMM route.
- **Metric:** paired Brier/AUROC, two-label mass, abstention coverage.
- **Completed finding:** Observed-row coverage 100%; exact-score preimages audited; approximate routes labelled.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Exactness is limited to declared discrete projected model.
- **Stop criterion:** Projected discrete score exactness checked with preimages, approximate routes labelled, zero-denominator policy stated and same-person predictions saved.
- **Unresolved wider scope:** Universal off-support coverage and exact copula/GMM probabilities.
- **Forbidden claim:** Exact rounded/clipped continuous score claim.
- **Evidence:** `docs/INTEGRITY_AND_PROJECTION_AUDIT.md`, `docs/PROJECTED_JOINT_PREDICTION_FINDINGS_20261025.md`.

## Experiment 8: Which queries fail?

- **Methods:** 10,500 development query answers, 175 queries; frozen official primary/audit answers.
- **Metric:** max/mean error, arity, support, named worst query.
- **Completed finding:** Official size primary mean 0.022216; dominant HS-grad/high-income query in 33/60 size draws.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Finite-workload maxima are reproducible and named.
- **Stop criterion:** All registered query definitions/answers and named maxima retained with arity/support and target-role labels; viewed audits are not called independent.
- **Unresolved wider scope:** Arbitrary-query guarantee; independent inference from viewed audit.
- **Forbidden claim:** Population TV or universal query accuracy.
- **Evidence:** `docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md`, `reports/final_build/confirmation_dominant_queries.csv`.

## Experiment 9: Which registered components explain results?

- **Methods:** 12 same-row projection, six fixed-checkpoint summary-access ablations, historical capacity comparison.
- **Metric:** paired primary/query errors and access bytes.
- **Completed finding:** Structural repair and access changes matter; no isolated component establishes a practical general weighting gain.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Component effects only for measured fixed-input contrasts.
- **Stop criterion:** Registered same-row projection and fixed-pilot summary-access contrasts terminal; any untested component effect is removed from retained claims.
- **Unresolved wider scope:** Irrelevant covariance/regularization factorial sweeps.
- **Forbidden claim:** Causal explanation from confounded historical versions.
- **Evidence:** `docs/EXP09_ABLATION_CLOSURE.md`, `reports/mechanisms/`.

## Experiment 10: How does controlled heterogeneity affect correction?

- **Methods:** Six G* fixed-quantity K5 cells at severity 0.25/0.85 and seeds711/722/733.
- **Metric:** achieved skew, local error, oracle headroom, fidelity.
- **Completed finding:** Registered contrasts terminal; fixed 1000 train/200 tune per client and equal-alpha mechanism target.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Severity findings apply to achieved empirical partitions.
- **Stop criterion:** Both non-IID severities and three seeds have fixed per-client quantities and achieved-skew diagnostics; empirical identity is not called population TV.
- **Unresolved wider scope:** Full causal isolation of assignment and conditional relationships.
- **Forbidden claim:** Population-TV decomposition or universal causal mechanism.
- **Evidence:** `docs/EXP10_MECHANISM_CLOSURE.md`, `reports/mechanisms/`.

## Experiment 11: What finite-query conditional transfer follows?

- **Methods:** Elementary proposition, binary counterexample, 48 bound rows and 5112 student/direct triangles.
- **Metric:** ratio bound, support denominator, empirical triangle.
- **Completed finding:** Algebra checked; rare support makes bounds weak and triggers abstention.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Finite-query bound under stated support assumptions.
- **Stop criterion:** Finite-query proposition, counterexample, support curves and saved empirical triangle checks agree on their denominators and assumptions.
- **Unresolved wider scope:** General arbitrary-condition theorem.
- **Forbidden claim:** Experimental proof of universal transfer.
- **Evidence:** `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md`, `docs/PROJECTED_TRANSFER_FINDINGS_20261025.md`.

## Experiment 12: What privacy, access and resource claims survive?

- **Methods:** Complete release ledger, atom-aware histogram epsilon1/4/8, four adapted FLAIM fits, three matched payload cells.
- **Metric:** adjacency/composition, serialized bytes, runtime, attack diagnostics.
- **Completed finding:** Main pipeline nonprivate; model+metadata 1.915-2.866x matched raw bytes; conditional histogram epsilon13 if three settings released.
- **Disposition:** `COMPLETE_BOUNDED_FINDING`. Separate conditional privacy reference and measured release costs.
- **Stop criterion:** Every released-object class has access/privacy provenance; matched payload units, histogram adjacency/composition and main nonprivate status are explicit.
- **Unresolved wider scope:** Whole-pipeline DP, WAN/security measurement and privacy-matched FLAIM ranking.
- **Forbidden claim:** End-to-end DP or compression assertion.
- **Evidence:** `docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md`, `reports/resources/`, `docs/PUBLISHED_REFERENCE_FINDINGS.md`.
