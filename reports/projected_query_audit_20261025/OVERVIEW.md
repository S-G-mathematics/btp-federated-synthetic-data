# Projected query-level development audit

Six fixed-model cells, two weight rules and five exactly reproduced 10,000-row draws each. All 175 registered primary/audit answers are saved; the unweighted pooled real target is secondary. Official Adult test was not evaluated.

## Query arity and alpha-support strata

| family | workload | arity | support_stratum | query_draw_rows | distinct_queries | size_abs_error_mean | constrained_abs_error_mean | constrained_minus_size_mean | size_abs_error_max | constrained_abs_error_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | primary | 1 | common_ge_5pct | 830 | 57 | 0.007958 | 0.009075 | 0.001117 | 0.032462 | 0.041526 |
| chow_liu_age_k5 | primary | 1 | low_1_to_5pct | 405 | 30 | 0.003742 | 0.003575 | -0.000167 | 0.014332 | 0.016575 |
| chow_liu_age_k5 | primary | 1 | rare_lt_1pct | 910 | 63 | 0.000878 | 0.000865 | -0.000014 | 0.005908 | 0.005403 |
| chow_liu_age_k5 | primary | 2 | common_ge_5pct | 60 | 4 | 0.017033 | 0.015444 | -0.001589 | 0.030235 | 0.029048 |
| chow_liu_age_k5 | primary | 2 | low_1_to_5pct | 60 | 4 | 0.007474 | 0.007292 | -0.000182 | 0.021398 | 0.020698 |
| chow_liu_age_k5 | primary | 2 | rare_lt_1pct | 15 | 1 | 0.000800 | 0.000840 | 0.000040 | 0.001300 | 0.001400 |
| chow_liu_age_k5 | unseen_audit | 3 | common_ge_5pct | 130 | 10 | 0.016338 | 0.017974 | 0.001637 | 0.051812 | 0.061812 |
| chow_liu_age_k5 | unseen_audit | 3 | low_1_to_5pct | 140 | 10 | 0.007805 | 0.007920 | 0.000114 | 0.025479 | 0.024505 |
| chow_liu_age_k5 | unseen_audit | 3 | rare_lt_1pct | 75 | 5 | 0.001469 | 0.001486 | 0.000017 | 0.004248 | 0.004067 |
| mixed_gmm_label_skew_k10 | primary | 1 | common_ge_5pct | 820 | 57 | 0.011295 | 0.011939 | 0.000645 | 0.065517 | 0.056032 |
| mixed_gmm_label_skew_k10 | primary | 1 | low_1_to_5pct | 415 | 31 | 0.003577 | 0.003693 | 0.000115 | 0.016962 | 0.014762 |
| mixed_gmm_label_skew_k10 | primary | 1 | rare_lt_1pct | 910 | 63 | 0.000936 | 0.001054 | 0.000117 | 0.005813 | 0.006306 |
| mixed_gmm_label_skew_k10 | primary | 2 | common_ge_5pct | 55 | 4 | 0.009294 | 0.025612 | 0.016319 | 0.036127 | 0.070827 |
| mixed_gmm_label_skew_k10 | primary | 2 | low_1_to_5pct | 65 | 5 | 0.007853 | 0.007018 | -0.000834 | 0.023595 | 0.018032 |
| mixed_gmm_label_skew_k10 | primary | 2 | rare_lt_1pct | 15 | 1 | 0.001347 | 0.001493 | 0.000147 | 0.002300 | 0.002500 |
| mixed_gmm_label_skew_k10 | unseen_audit | 3 | common_ge_5pct | 125 | 9 | 0.023967 | 0.028280 | 0.004313 | 0.070688 | 0.058888 |
| mixed_gmm_label_skew_k10 | unseen_audit | 3 | low_1_to_5pct | 145 | 10 | 0.006135 | 0.006084 | -0.000051 | 0.016001 | 0.019007 |
| mixed_gmm_label_skew_k10 | unseen_audit | 3 | rare_lt_1pct | 75 | 5 | 0.001690 | 0.001642 | -0.000048 | 0.005218 | 0.004369 |

## Primary draw maxima

| family | method | primary_query_linf_mean | primary_query_linf_min_draw | primary_query_linf_max_draw |
| --- | --- | --- | --- | --- |
| chow_liu_age_k5 | constrained | 0.032989 | 0.024835 | 0.041526 |
| chow_liu_age_k5 | size | 0.028363 | 0.025335 | 0.032462 |
| mixed_gmm_label_skew_k10 | constrained | 0.053559 | 0.040123 | 0.070827 |
| mixed_gmm_label_skew_k10 | size | 0.055305 | 0.047182 | 0.065517 |

The simultaneous radius in conditional_uncertainty.csv follows a Hoeffding/union calculation under independent bounded real and synthetic sampling. Its assumptions are not verified for the Adult records or overlapping splits; it is not a measured population-TV distance or a validated confidence interval. The audit workload has been inspected during development and is not independent confirmation.
