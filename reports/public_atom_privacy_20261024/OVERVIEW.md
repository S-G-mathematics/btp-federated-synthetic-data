# Public zero-atom histogram development audit

Six fixed Adult development cells, five public synthetic draws per mechanism. The private and nonprivate histograms share the same public zero atoms, bins and education projection. Official Adult test was not evaluated.

| family | method | query_linf_mean | query_linf_min_seed | query_linf_max_seed | unseen_query_linf_mean | gain_zero_abs_error_mean | loss_zero_abs_error_mean | model_bytes_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | epsilon_1 | 0.337651 | 0.332737 | 0.346279 | 0.049462 | 0.024557 | 0.021197 | 13818.000000 |
| chow_liu_age_k5 | epsilon_4 | 0.330778 | 0.328437 | 0.332679 | 0.047460 | 0.010430 | 0.005380 | 13818.000000 |
| chow_liu_age_k5 | epsilon_8 | 0.332391 | 0.329017 | 0.335839 | 0.047081 | 0.006990 | 0.004775 | 13818.000000 |
| chow_liu_age_k5 | nonprivate | 0.332158 | 0.328517 | 0.335619 | 0.046944 | 0.006317 | 0.003040 | 13725.000000 |
| mixed_gmm_label_skew_k10 | epsilon_1 | 0.336803 | 0.332118 | 0.342274 | 0.052812 | 0.033822 | 0.036618 | 25727.333333 |
| mixed_gmm_label_skew_k10 | epsilon_4 | 0.335477 | 0.330458 | 0.338754 | 0.048589 | 0.013809 | 0.009538 | 25727.333333 |
| mixed_gmm_label_skew_k10 | epsilon_8 | 0.334850 | 0.331298 | 0.341094 | 0.047819 | 0.010816 | 0.005318 | 25727.333333 |
| mixed_gmm_label_skew_k10 | nonprivate | 0.334530 | 0.330498 | 0.340714 | 0.047618 | 0.006909 | 0.002202 | 25549.333333 |

## Likelihood membership diagnostic (not a DP proof)

| family | method | client_models | mean_likelihood_membership_auc | min_likelihood_membership_auc | max_likelihood_membership_auc | finite_score_fraction_min |
| --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | epsilon_1 | 15 | 0.501362 | 0.476267 | 0.524295 | 1.000000 |
| chow_liu_age_k5 | epsilon_4 | 15 | 0.503918 | 0.477672 | 0.530439 | 1.000000 |
| chow_liu_age_k5 | epsilon_8 | 15 | 0.503472 | 0.477428 | 0.533169 | 1.000000 |
| chow_liu_age_k5 | nonprivate | 15 | 0.503223 | 0.477994 | 0.532058 | 1.000000 |
| mixed_gmm_label_skew_k10 | epsilon_1 | 30 | 0.507603 | 0.326531 | 0.629126 | 1.000000 |
| mixed_gmm_label_skew_k10 | epsilon_4 | 30 | 0.506082 | 0.386719 | 0.661415 | 1.000000 |
| mixed_gmm_label_skew_k10 | epsilon_8 | 30 | 0.503581 | 0.346939 | 0.626291 | 1.000000 |
| mixed_gmm_label_skew_k10 | nonprivate | 30 | 0.505403 | 0.358025 | 0.680000 | 1.000000 |

A single fresh-noise private histogram release per fixed public client membership/size has its stated epsilon-DP scope. Publishing all three epsilon settings on one client would compose to epsilon=13. The research bundle also contains nonprivate releases and raw data; the full pipeline is not DP. Overlapping split seeds and data-dependent assignment are outside the single-release guarantee.
