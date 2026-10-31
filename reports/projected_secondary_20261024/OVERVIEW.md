# Projected secondary development audit

Six registered cells; official Adult test was not evaluated. Three development split seeds reuse people and are not independent cohorts. Five synthetic draws per method/cell measure subgroup sampling variation; one train/tune/calibration draw supplies each predictive fit.

## Utility: constrained minus size

| family | learner | delta_auroc_mean | delta_auroc_min | delta_auroc_max | delta_brier_mean | delta_brier_min | delta_brier_max | auroc_noninferior_margin_minus_0p01 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | extra_trees | 0.01461 | 0.00766 | 0.02168 | -0.00294 | -0.00532 | 0.00000 | True |
| chow_liu_age_k5 | logistic | 0.00408 | -0.00446 | 0.01100 | -0.00173 | -0.00455 | 0.00007 | True |
| mixed_gmm_label_skew_k10 | extra_trees | 0.00015 | -0.00285 | 0.00573 | 0.00063 | -0.00185 | 0.00488 | True |
| mixed_gmm_label_skew_k10 | logistic | 0.00071 | -0.00290 | 0.00554 | 0.00177 | -0.00112 | 0.00586 | True |

## Supported subgroup maximum prevalence error: constrained minus size

| family | delta_max_error_mean | delta_max_error_min_seed | delta_max_error_max_seed | subgroup_noninferior_margin_plus_0p01 |
| --- | --- | --- | --- | --- |
| chow_liu_age_k5 | 0.01510 | -0.00158 | 0.02724 | False |
| mixed_gmm_label_skew_k10 | -0.00926 | -0.01168 | -0.00608 | True |

Negative differences favour constrained weighting. The privileged real-trained TRTR is a separate diagnostic, not a server release. These are selected exploratory cells, not a global method-selection basis. Raw predictions and all client metrics remain in the cell outputs.
