# Frozen official Adult confirmation — 25 October 2026

The complete campaign freeze `SELECTION_FROZEN.json` has canonical SHA-256 `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. The gate accepted it before the **first official-test confirmation-scoring read at 2026-10-25T05:40:33.072893Z**. Raw test records were read earlier solely for source validation and duplicate quarantine, as documented in `docs/TEST_ACCESS_SCOPE_CLARIFICATION.md`. The official Adult test has 16,281 people/rows and was not used for family, weight, threshold or learner selection. Seeds404/505 are partition/model replications on those **same people**, not independent cohorts. The frozen family is projected copula, selected from Adult validation only; its main weights are `w=alpha` from client training mass. Its mixed-data scores remain approximate.

All 12 registered cells (age, age+education, label-skew × K5/K10 × seeds404/505) completed, with no failed/unsupported primary or secondary cell. Each method used the same cell's locally tuned client checkpoints and five independent 10,000-row draws, exactly allocated by largest remainder. The evaluator used the fixed alpha-standardized official-test query answer as primary and retained the ordinary pooled answer separately. The constrained rule saw only permitted unnoised aggregate calibration query means and a 1,500-row/client model pilot. It satisfied `||w-alpha||_1<=0.25`, `w_i>=0.5 alpha_i`; mean achieved L1 was 0.2483. No test query entered weight fitting.

## Primary fidelity

| Partition | K | Size mean query-max | Constrained minus size | Uniform minus size |
| --- | ---: | ---: | ---: | ---: |
| Age | 5 | 0.025883 | +0.000043 | -0.001019 |
| Age | 10 | 0.026583 | -0.000156 | +0.042807 |
| Age+education | 5 | 0.022456 | -0.000579 | +0.000420 |
| Age+education | 10 | 0.022922 | -0.000823 | -0.000241 |
| Label skew | 5 | 0.018286 | +0.000276 | +0.142920 |
| Label skew | 10 | 0.017164 | -0.000050 | +0.061946 |
| **Equal mean over 12 cells** | | **0.022216** | **-0.000215** | **+0.041139** |

Negative differences favour the challenger. The registered practical margin was **-0.005**; no partition/K two-seed slice met it. Frozen official-holdout results were consistent with the bounded development decision to retain size weighting under the stated target and release contract. The same official people recur across these cells, so this is not independent-cohort confirmation. It does not prove equivalence or rule out smaller gains. Uniform weighting badly changed label-skew target representation, especially at K5. All 180 synthetic draws and per-query answers are saved. The size method's worst primary query was `education=HS-grad & income>50K` in 33/60 draws, followed by `sex=Female & income>50K` in 14/60; the maximum is a named finite-workload quantity, not population TV. Mean unseen/viewed-audit query-max was 0.022552 size, 0.022294 constrained and 0.030435 uniform. This audit workload had already been inspected during development and is a registered secondary endpoint, not a fresh independent discovery sample.

## Probability prediction and conditional support

Paired official-test predictions were saved for a tuned logistic model and 120-tree extra-trees model, trained and Platt-calibrated on separate source-specific train/tune/calibration sets. In each of the 12 cells, privileged real TRTR used 21,148 real training rows, 4,880 real tuning rows and 3,254 real calibration rows. Each synthetic TSTR method used 10,000 generated training rows, 2,000 generated tuning rows and 2,000 independently generated calibration rows. TRTR therefore had a larger training budget; the comparison describes the registered budgets, not an intrinsic matched-size real-versus-synthetic effect. The table gives equal cell means of alpha-weighted global metrics; the same official people were scored within a cell.

| Learner | Training source | Brier ↓ | AUROC ↑ |
| --- | --- | ---: | ---: |
| Logistic | Real TRTR, privileged | 0.101987 | 0.904646 |
| Logistic | Synthetic size | 0.129818 | 0.856167 |
| Logistic | Synthetic constrained | 0.129254 | 0.857161 |
| Logistic | Synthetic uniform | 0.132903 | 0.857331 |
| Extra trees | Real TRTR, privileged | 0.105741 | 0.899013 |
| Extra trees | Synthetic size | 0.133218 | 0.846439 |
| Extra trees | Synthetic constrained | 0.132705 | 0.846115 |
| Extra trees | Synthetic uniform | 0.138131 | 0.848441 |

The real-trained reference has a materially better Brier and AUROC than synthetic-trained methods **at these registered and unequal training budgets**. No matched-size learning curve was run. The constrained method's roughly 0.0005 Brier improvement over synthetic size is descriptive and not a registered practical gain claim. Per-client counts, class support and probabilities are in each cell's utility files; AUROC is marked unsupported below 20 positives or 20 negatives.

For the selected size teacher, an independent 30,000-row generated support pilot preceded each registered request, with at least 300 matches and 1% mass required. Direct rejection then targeted 1,000 accepted rows under a 200,000-proposal cap. Across 12 cells, age25–45, female and bachelors+age30–60 requests completed with **zero accepted-condition violations**. Mean feature-query maxima were respectively 0.08379, 0.37500 and 0.14701. The **female-condition worst feature query was `relationship=Husband` in all 12 cells**: its alpha-standardized real conditional frequency was zero in these reference records, while generated frequencies ranged from 0.340 to 0.399, giving mean absolute discrepancy 0.375. This is an observed sex/relationship dependency failure of the frozen model in this benchmark, not a universal demographic rule. The first two requests accepted in 10,000 proposals per cell; bachelors averaged 12,500 proposals. The doctorate+age60–90 request abstained for low teacher support in **all 12 cells**, with no real held-out count used in that decision. Exact satisfaction of the requested filter does not validate other generated features. This service supports structured public-schema Boolean requests but offers no arbitrary-condition accuracy certificate.

## Interpretation and reproducibility

Development design was assessment informed: projection, workloads and support rules were repaired after earlier exploratory assessment. The **final family selection** itself used registered validation rows only, and the official test was opened only after the full written freeze. The same official people recur under different client assignments; five draws estimate synthesis variation conditional on fitted models, and two seeds do not justify a narrow population confidence interval. The Bank external batch is a separate dataset replication but may contain repeated contacts without person IDs.

Raw evidence: `results/adult_confirmation_20261025/` contains cell configurations, source/split/model manifests, local tuning tables, checkpoints, allowed summaries, solver certificates, five synthetic draws per method, per-query answers, utility models/predictions, condition support and accepted samples, and completion hashes. Aggregate rebuild: `reports/final_build/confirmation_{all_draws,cell_means,paired_cells,slices,dominant_queries,query_summary,utility,utility_paired,conditional}.csv` and `adult_frozen_confirmation.png`. Test access: `reports/confirmation/FIRST_OFFICIAL_TEST_READ.json`. Logs: `logs/adult_confirmation_primary_20261025.log`, `adult_confirmation_secondary_20261025.log`. The clean-room check regenerated the first size draw byte-for-byte (SHA-256 `973e04cbd4e9845031ffc2d30532e6102a0beaa5ab4bfb75e0e0bd9ff498c30e`) and reproduced its primary maximum from the named query; see `logs/verify_final_package_20261025.log`.
