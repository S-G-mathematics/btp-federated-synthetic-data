# Projected secondary development findings — 24 October 2026 UTC

## What ran and where

The predeclared six-cell audit in `docs/PROJECTED_SECONDARY_PROTOCOL_20261024.md` ran on the existing EC2 under the shared heavy-compute lease, one worker and one native thread. It covered Chow-Liu/age/K5 and mixed-GMM/label-skew/K10 at development seeds 101, 202 and 303. Each cell compared tuned projected **size** and the fixed **constrained** query-minimax weights, with five independent 10,000-row subgroup draws per method. Its first draw, separate 3,000-row tune draw and separate 3,000-row calibration draw trained and calibrated logistic and extra-trees income predictors. The privileged pooled-real same-learner TRTR reference was fitted separately. The official Adult test and seeds 404/505 were not evaluated.

EC2 evidence: `results/projected_secondary_20261024/<cell>/` contains configuration, subgroup query answers, global/per-client utility metrics, raw paired predictions, settings and model checkpoints. `reports/projected_secondary_20261024/` contains the audited aggregate and per-cell CSVs and overview. Logs: `logs/projected_secondary_initial_20261024.log`, `logs/projected_secondary_remaining_20261024.log`, `logs/ec2_tests_projected_secondary_20261024.log` (76 passed). The lightweight report tables are also copied to the laptop under `reports/projected_secondary_local_20261024/`. All six cells completed; no `failure.json` exists. The pinned model source hash in the saved cells is `25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868`.

## Paired findings

| Fixed cell family, three overlapping split seeds | Constrained minus size primary query max, mean | Constrained minus size maximum supported-subgroup error, mean over seeds and five draws | Logistic AUROC difference, mean (seed range) | Extra-trees AUROC difference, mean (seed range) |
| --- | ---: | ---: | ---: | ---: |
| Chow-Liu / age / K5 | +0.004626 | +0.015095 | +0.004080 (−0.004461 to +0.010998) | +0.014610 (+0.007663 to +0.021680) |
| Mixed GMM / label skew / K10 | −0.001746 | −0.009256 | +0.000707 (−0.002899 to +0.005544) | +0.000153 (−0.002853 to +0.005731) |

Negative query/subgroup differences and positive AUROC differences favour constrained weighting. The registered primary practical gain margin was −0.005; neither family reaches it on the three-seed mean. Chow-Liu age **fails** the provisional subgroup noninferiority margin of +0.01 despite utility gains. Mixed GMM label skew **passes** the subgroup and AUROC noninferiority margins, but does not reach practical primary gain. All four family/learner AUROC means pass the −0.01 noninferiority tolerance. This is a descriptive screen, not a statistical equivalence result. The five synthetic draws capture generation variation, while the three Adult split seeds reuse people.

For scale, mean size-weighted AUROC was 0.836700 logistic and 0.820088 extra-trees in Chow-Liu age, versus privileged TRTR 0.897470 and 0.892462. In mixed-GMM label skew, size AUROC was 0.884271 and 0.868851 versus privileged TRTR 0.897574 and 0.892642. Synthetic training did not outperform real training in these summaries. TRTR has broader data access and is not a federated server release. Full Brier, AUPRC, calibration, F1, client-level metrics and row-level predictions are retained; a single-class client's undefined discrimination metric is never imputed.

## Decision and limits

**No improved weighting rule is established for the fixed-alpha application.** These two selected exploratory slices do not justify a global winner or an official-test run. Size weighting remains the provisional fallback. The projected pipeline and released unnoised summaries are nonprivate; this audit adds privileged real assessment and pooled-real TRTR fitting. No campaign-wide `SELECTION_FROZEN.json` has been created. The registered audit workload was already seen during development and cannot become independent confirmation.

Next executable work: quantify pilot and synthetic-sample uncertainty for size versus constrained weights on these same two families, audit conditional support and the complete release/resource ledger, and then write a campaign-wide development decision memo. If the registered gates remain unmet, freeze and report “no improved weighting method established” before any optional confirmation. Do not select a method from official-test outcomes.
