# Fixed development conditional transfer audit

Six projected model cells, two fixed weights, four registered conditions, 30,000-row reconstructed teacher per method/cell. Official Adult test was not used.

## Empirical ratio bounds by real support

| family | method | condition | support_status | cells | real_mass_mean | teacher_mass_mean | teacher_count_min | observed_conditional_linf_mean | empirical_ratio_bound_mean | bound_minus_observed_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | constrained | age25-45 | supported | 3 | 0.546101 | 0.526611 | 14806 | 0.036501 | 0.120754 | 0.084254 |
| chow_liu_age_k5 | constrained | bachelors_age30-60 | supported | 3 | 0.113722 | 0.109022 | 3027 | 0.104557 | 0.251408 | 0.146851 |
| chow_liu_age_k5 | constrained | female | supported | 3 | 0.326772 | 0.332800 | 9836 | 0.107882 | 0.128524 | 0.020641 |
| chow_liu_age_k5 | constrained | rare_doctorate_age60-90 | abstain | 3 | 0.002050 | 0.001367 | 30 | 0.569919 | 0.895983 | 0.326064 |
| chow_liu_age_k5 | size | age25-45 | supported | 3 | 0.546101 | 0.517678 | 15382 | 0.037226 | 0.126101 | 0.088875 |
| chow_liu_age_k5 | size | bachelors_age30-60 | supported | 3 | 0.113722 | 0.107144 | 3005 | 0.101536 | 0.238277 | 0.136741 |
| chow_liu_age_k5 | size | female | supported | 3 | 0.326772 | 0.330700 | 9836 | 0.106624 | 0.139552 | 0.032928 |
| chow_liu_age_k5 | size | rare_doctorate_age60-90 | abstain | 3 | 0.002050 | 0.001478 | 41 | 0.612371 | 0.888146 | 0.275775 |
| mixed_gmm_label_skew_k10 | constrained | age25-45 | supported | 3 | 0.545147 | 0.533156 | 15745 | 0.068545 | 0.102046 | 0.033502 |
| mixed_gmm_label_skew_k10 | constrained | bachelors_age30-60 | supported | 3 | 0.112134 | 0.116800 | 3454 | 0.148342 | 0.193902 | 0.045559 |
| mixed_gmm_label_skew_k10 | constrained | female | supported | 3 | 0.328486 | 0.336522 | 10055 | 0.348076 | 0.383596 | 0.035520 |
| mixed_gmm_label_skew_k10 | constrained | rare_doctorate_age60-90 | abstain | 3 | 0.002085 | 0.001156 | 22 | 0.606104 | 0.877148 | 0.271044 |
| mixed_gmm_label_skew_k10 | size | age25-45 | supported | 3 | 0.545147 | 0.530378 | 15635 | 0.076792 | 0.116580 | 0.039788 |
| mixed_gmm_label_skew_k10 | size | bachelors_age30-60 | supported | 3 | 0.112134 | 0.121622 | 3590 | 0.136443 | 0.241525 | 0.105083 |
| mixed_gmm_label_skew_k10 | size | female | supported | 3 | 0.328486 | 0.326122 | 9721 | 0.357661 | 0.379774 | 0.022113 |
| mixed_gmm_label_skew_k10 | size | rare_doctorate_age60-90 | abstain | 3 | 0.002085 | 0.001100 | 32 | 0.533898 | 0.979392 | 0.445494 |

## Matched-row independent direct teacher versus postfiltered student

| family | method | condition | query_rows | student_real_abs_mean | direct_real_abs_mean | student_direct_abs_mean | student_real_abs_max | direct_real_abs_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | constrained | age25-45 | 426 | 0.008236 | 0.006508 | 0.007341 | 0.071195 | 0.048905 |
| chow_liu_age_k5 | constrained | bachelors_age30-60 | 426 | 0.012628 | 0.011572 | 0.006983 | 0.218900 | 0.141674 |
| chow_liu_age_k5 | constrained | female | 426 | 0.012086 | 0.011196 | 0.005038 | 0.124425 | 0.128934 |
| chow_liu_age_k5 | size | age25-45 | 426 | 0.008491 | 0.006089 | 0.006477 | 0.074484 | 0.036982 |
| chow_liu_age_k5 | size | bachelors_age30-60 | 426 | 0.013123 | 0.011049 | 0.006828 | 0.184878 | 0.112384 |
| chow_liu_age_k5 | size | female | 426 | 0.011608 | 0.010383 | 0.005198 | 0.114396 | 0.119916 |
| mixed_gmm_label_skew_k10 | constrained | age25-45 | 426 | 0.010062 | 0.008019 | 0.007188 | 0.164494 | 0.080228 |
| mixed_gmm_label_skew_k10 | constrained | bachelors_age30-60 | 426 | 0.016641 | 0.013656 | 0.006332 | 0.224335 | 0.154885 |
| mixed_gmm_label_skew_k10 | constrained | female | 426 | 0.020858 | 0.020311 | 0.005769 | 0.352028 | 0.356857 |
| mixed_gmm_label_skew_k10 | size | age25-45 | 426 | 0.009836 | 0.007547 | 0.006723 | 0.141071 | 0.096715 |
| mixed_gmm_label_skew_k10 | size | bachelors_age30-60 | 426 | 0.014895 | 0.012794 | 0.005851 | 0.238065 | 0.178692 |
| mixed_gmm_label_skew_k10 | size | female | 426 | 0.021742 | 0.021397 | 0.005996 | 0.365915 | 0.374374 |

The bound is deterministic for finite empirical measures and declared queries, conditional on positive real and teacher support. Rare-condition rows remain operational abstentions even when a mathematical ratio is computed. The direct teacher uses an independent synthetic pool; the student/direct term includes sampling noise. Adult split seeds overlap, and this is not population-TV estimation or arbitrary-condition generalization.
