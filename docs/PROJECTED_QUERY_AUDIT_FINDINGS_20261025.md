# Projected query-level development audit: findings

**25 October 2026 local time.** The protocol was fixed in `docs/PROJECTED_QUERY_AUDIT_PROTOCOL_20261025.md` before these runs. This is development-assessment evidence on Adult; the official test and confirmation seeds 404/505 were not used.

## Execution and target

All six registered cells completed on `ip-172-31-11-178` under the shared one-worker lease: projected Chow-Liu age/K=5 and projected mixed GMM label-skew/K=10, each at split seeds 101/202/303. For size and fixed constrained weights, five 10,000-row draws per cell were regenerated from the saved client checkpoints and public seeds. Every regenerated primary query maximum agreed with the prior saved result to within `1e-10`. There are 150 primary and 25 unseen-audit queries, yielding 10,500 saved per-query method/draw answers. No cell failed; the EC2 suite passed 79 tests. Raw cell configurations, answers and logs remain under `results/projected_query_audit_20261025/` and `logs/projected_query_audit_{initial,remaining,report}_20261025.log`; aggregates are in `reports/projected_query_audit_20261025/` and a laptop copy in `reports/projected_query_audit_local_20261025/`.

The primary real reference is the **alpha-standardized client mixture** on development assessment, with `alpha` fixed from declared training client mass. Unweighted pooled held-out answers are separate secondary columns. Their primary-workload maximum discrepancy reached 0.004398 across Chow-Liu cells and 0.009984 across GMM cells; therefore silently substituting the pooled reference could materially alter a 0.005 practical-gain decision.

## Measured query differences

| Family | Size mean primary max | Constrained mean primary max | Constrained minus size |
| --- | ---: | ---: | ---: |
| Chow-Liu age/K5 | 0.028363 | 0.032989 | +0.004626 |
| Mixed GMM label-skew/K10 | 0.055305 | 0.053559 | -0.001746 |

The means use 3 overlapping Adult splits and 5 synthetic draws per split, not 15 independent cohorts. Neither constrained family meets the predeclared -0.005 practical-gain margin. On the primary workload, constrained Chow-Liu worsened mean absolute error on common one-way queries by 0.001117, although common two-way mean improved by 0.001589. Constrained GMM worsened common two-way mean absolute error by 0.016319 even while its primary **maximum** improved slightly on average. On the unseen-audit three-way common-support queries, constrained mean absolute error worsened by 0.001637 for Chow-Liu and 0.004313 for GMM. These are descriptive strata of the registered finite workload, not a new independent test set.

The dominant primary Chow-Liu queries include age thresholds and education/income conjunctions. The GMM constrained primary maximum was most often `sex=Male&income>50K` (11 of 15 draws), whereas GMM size was most often dominated by `age<=35` (11 of 15). The unseen-audit maximum often involved `age17-30&Male&<=50K`. Full query names, both real targets, synthetic answers, signed errors and support strata are saved; no query was fed back into a weight refit here.

The simultaneous 95% Hoeffding/union **conditional reference radius** over 175 bounded queries was 0.05597–0.05665 across cells, using the stated independent-real/independent-synthetic sampling assumptions. Adult sampling and overlapping split seeds do not validate those assumptions. This radius is not a measured population distance or a validated confidence interval for these records. The five draws separately reveal synthetic sampling variability. Rare-query relative errors and population-TV claims are not inferred.

## Decision and limits

This audit reinforces the existing development draft: no practical fixed-target weighting gain has been established; tuned size weighting remains the provisional fallback. It does not prove size weighting optimal, establish equal-access method superiority, or justify opening official test. The audit workload has already been viewed in development. A campaign-wide generator/procedure freeze, remaining claim-specific ablations and independent external replication remain open.
