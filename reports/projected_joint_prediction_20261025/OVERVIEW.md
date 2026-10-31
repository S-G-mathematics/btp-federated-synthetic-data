# Projected joint-implied income development audit

Chow-Liu is exact for its fitted projected discrete model. Mixed GMM uses a normalized approximate score. All comparisons are on the same covered development-assessment people, with alpha-standardized global weights. Official Adult test was not evaluated.

## Coverage

| family | joint_method | n_min | alpha_coverage_mean | alpha_coverage_min_seed | off_support_rows_total | nonfinite_rows_total |
| --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | constrained | 1613 | 1.000000 | 1.000000 | 0 | 0 |
| chow_liu_age_k5 | size | 1613 | 1.000000 | 1.000000 | 0 | 0 |
| mixed_gmm_label_skew_k10 | constrained | 1613 | 1.000000 | 1.000000 | 0 | 0 |
| mixed_gmm_label_skew_k10 | size | 1613 | 1.000000 | 1.000000 | 0 | 0 |

## Predictive scores

| family | joint_method | predictor | auroc_mean | auroc_min_seed | auroc_max_seed | auprc_mean | brier_mean | log_loss_mean | ece_fixed10_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | constrained | TRTR_privileged_extra_trees | 0.892462 | 0.886895 | 0.896239 | 0.730654 | 0.112242 | 0.349165 | 0.026247 |
| chow_liu_age_k5 | constrained | TRTR_privileged_logistic | 0.897470 | 0.892571 | 0.902601 | 0.748205 | 0.109576 | 0.341367 | 0.030601 |
| chow_liu_age_k5 | constrained | joint_implied | 0.843437 | 0.840924 | 0.846057 | 0.649633 | 0.128540 | 0.391694 | 0.021847 |
| chow_liu_age_k5 | constrained | synthetic_extra_trees | 0.834698 | 0.828063 | 0.845948 | 0.615783 | 0.136560 | 0.413783 | 0.028024 |
| chow_liu_age_k5 | constrained | synthetic_logistic | 0.840781 | 0.835217 | 0.848232 | 0.626076 | 0.136221 | 0.411808 | 0.036342 |
| chow_liu_age_k5 | size | TRTR_privileged_extra_trees | 0.892462 | 0.886895 | 0.896239 | 0.730654 | 0.112242 | 0.349165 | 0.026247 |
| chow_liu_age_k5 | size | TRTR_privileged_logistic | 0.897470 | 0.892571 | 0.902601 | 0.748205 | 0.109576 | 0.341367 | 0.030601 |
| chow_liu_age_k5 | size | joint_implied | 0.843927 | 0.841260 | 0.846094 | 0.650062 | 0.128481 | 0.391372 | 0.020822 |
| chow_liu_age_k5 | size | synthetic_extra_trees | 0.820088 | 0.815596 | 0.824268 | 0.590193 | 0.139501 | 0.422005 | 0.027201 |
| chow_liu_age_k5 | size | synthetic_logistic | 0.836700 | 0.829513 | 0.843353 | 0.622626 | 0.137953 | 0.416201 | 0.036893 |
| mixed_gmm_label_skew_k10 | constrained | TRTR_privileged_extra_trees | 0.892642 | 0.885947 | 0.897688 | 0.724622 | 0.110659 | 0.344641 | 0.025442 |
| mixed_gmm_label_skew_k10 | constrained | TRTR_privileged_logistic | 0.897574 | 0.892428 | 0.903618 | 0.741918 | 0.108153 | 0.337315 | 0.029850 |
| mixed_gmm_label_skew_k10 | constrained | joint_implied | 0.861201 | 0.853654 | 0.867884 | 0.688560 | 0.130553 | 0.404156 | 0.062593 |
| mixed_gmm_label_skew_k10 | constrained | synthetic_extra_trees | 0.869003 | 0.863809 | 0.871984 | 0.680112 | 0.124312 | 0.385060 | 0.045105 |
| mixed_gmm_label_skew_k10 | constrained | synthetic_logistic | 0.884977 | 0.875330 | 0.890653 | 0.717278 | 0.118031 | 0.367635 | 0.050625 |
| mixed_gmm_label_skew_k10 | size | TRTR_privileged_extra_trees | 0.892642 | 0.885947 | 0.897688 | 0.724622 | 0.110659 | 0.344641 | 0.025442 |
| mixed_gmm_label_skew_k10 | size | TRTR_privileged_logistic | 0.897574 | 0.892428 | 0.903618 | 0.741918 | 0.108153 | 0.337315 | 0.029850 |
| mixed_gmm_label_skew_k10 | size | joint_implied | 0.861302 | 0.852208 | 0.865903 | 0.690434 | 0.126214 | 0.392454 | 0.049231 |
| mixed_gmm_label_skew_k10 | size | synthetic_extra_trees | 0.868851 | 0.866230 | 0.874070 | 0.682372 | 0.123680 | 0.385810 | 0.052967 |
| mixed_gmm_label_skew_k10 | size | synthetic_logistic | 0.884271 | 0.878229 | 0.889475 | 0.714085 | 0.116265 | 0.366003 | 0.046488 |

The paired-differences CSV contains joint minus trained-predictor AUROC/Brier/log-loss by split seed. TRTR is a privileged pooled-real diagnostic. Coverage says only whether the fitted route assigns support; it does not establish conditional correctness. Overlapping Adult splits are not independent cohorts.
