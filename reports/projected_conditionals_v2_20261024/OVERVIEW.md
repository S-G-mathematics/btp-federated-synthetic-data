# Projected registered-condition development audit

Six fixed-model cells; direct rejection uses an independent 30,000-row pool and matches the accepted student row count. Server support is decided from synthetic teacher counts only. Official Adult test was not evaluated.

## Route query errors

| family | condition | method | cells | direct_query_linf_mean | student_query_linf_mean | student_minus_direct_mean | student_minus_direct_min_seed | student_minus_direct_max_seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | age25-45 | constrained | 3 | 0.040319 | 0.065937 | 0.025619 | 0.012013 | 0.037958 |
| chow_liu_age_k5 | age25-45 | size | 3 | 0.036158 | 0.069892 | 0.033734 | 0.027398 | 0.037502 |
| chow_liu_age_k5 | bachelors_age30-60 | constrained | 3 | 0.119548 | 0.142656 | 0.023108 | -0.016440 | 0.077225 |
| chow_liu_age_k5 | bachelors_age30-60 | size | 3 | 0.104870 | 0.136704 | 0.031834 | 0.007138 | 0.073901 |
| chow_liu_age_k5 | female | constrained | 3 | 0.110433 | 0.106760 | -0.003673 | -0.012525 | 0.006015 |
| chow_liu_age_k5 | female | size | 3 | 0.110975 | 0.112472 | 0.001498 | -0.009519 | 0.008504 |
| mixed_gmm_label_skew_k10 | age25-45 | constrained | 3 | 0.065541 | 0.137889 | 0.072347 | 0.049001 | 0.107120 |
| mixed_gmm_label_skew_k10 | age25-45 | size | 3 | 0.084292 | 0.121190 | 0.036898 | 0.007629 | 0.064718 |
| mixed_gmm_label_skew_k10 | bachelors_age30-60 | constrained | 3 | 0.145561 | 0.195674 | 0.050112 | 0.021319 | 0.083168 |
| mixed_gmm_label_skew_k10 | bachelors_age30-60 | size | 3 | 0.146748 | 0.193057 | 0.046309 | 0.019216 | 0.060339 |
| mixed_gmm_label_skew_k10 | female | constrained | 3 | 0.352127 | 0.346956 | -0.005171 | -0.016517 | 0.002003 |
| mixed_gmm_label_skew_k10 | female | size | 3 | 0.369236 | 0.354045 | -0.015191 | -0.027528 | -0.001003 |

## Support and abstention

| family | condition | method | status | rows | real_count_min | teacher_matches_min |
| --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | age25-45 | constrained | completed | 6 | 881 | 14806 |
| chow_liu_age_k5 | age25-45 | size | completed | 6 | 881 | 15382 |
| chow_liu_age_k5 | bachelors_age30-60 | constrained | completed | 6 | 174 | 3027 |
| chow_liu_age_k5 | bachelors_age30-60 | size | completed | 6 | 174 | 3005 |
| chow_liu_age_k5 | female | constrained | completed | 6 | 519 | 9836 |
| chow_liu_age_k5 | female | size | completed | 6 | 519 | 9836 |
| chow_liu_age_k5 | rare_doctorate_age60-90 | constrained | abstain_insufficient_teacher_support | 3 | 3 | 30 |
| chow_liu_age_k5 | rare_doctorate_age60-90 | size | abstain_insufficient_teacher_support | 3 | 3 | 41 |
| mixed_gmm_label_skew_k10 | age25-45 | constrained | completed | 6 | 881 | 15745 |
| mixed_gmm_label_skew_k10 | age25-45 | size | completed | 6 | 881 | 15635 |
| mixed_gmm_label_skew_k10 | bachelors_age30-60 | constrained | completed | 6 | 174 | 3454 |
| mixed_gmm_label_skew_k10 | bachelors_age30-60 | size | completed | 6 | 174 | 3590 |
| mixed_gmm_label_skew_k10 | female | constrained | completed | 6 | 519 | 10055 |
| mixed_gmm_label_skew_k10 | female | size | completed | 6 | 519 | 9721 |
| mixed_gmm_label_skew_k10 | rare_doctorate_age60-90 | constrained | abstain_insufficient_teacher_support | 3 | 3 | 22 |
| mixed_gmm_label_skew_k10 | rare_doctorate_age60-90 | size | abstain_insufficient_teacher_support | 3 | 3 | 32 |

Positive student-minus-direct error favours direct rejection. These students are fitted separately for the four registered conditions; no cross-condition generalization is demonstrated. Three split seeds reuse Adult people.
