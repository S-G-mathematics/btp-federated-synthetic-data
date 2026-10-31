# Projected pilot sensitivity development audit

Six cells, four pilot sizes and five independent pilot seeds per size. Saved source H reproduced exactly in every cell. Official Adult test was not evaluated.

| family | pilot_per_client | H_error_mean | weight_l1_from_source_mean | fixed_reference_excess_mean | same_target_fixed_reference_excess_mean | fresh_delta_primary_mean | fresh_delta_primary_min_seed | fresh_delta_primary_max_seed | fresh_delta_unseen_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | 500 | 0.055407 | 0.395590 | 0.006684 | 0.003247 | 0.007153 | 0.002927 | 0.015326 | 0.000568 |
| chow_liu_age_k5 | 1500 | 0.033276 | 0.350466 | 0.008602 | 0.003770 | 0.003376 | -0.000618 | 0.009433 | 0.002953 |
| chow_liu_age_k5 | 5000 | 0.020778 | 0.311944 | 0.007941 | 0.001903 | 0.001183 | -0.002008 | 0.003134 | 0.002828 |
| chow_liu_age_k5 | 15000 | 0.011480 | 0.352724 | 0.004918 | 0.000832 | 0.000262 | -0.000907 | 0.001920 | 0.000632 |
| mixed_gmm_label_skew_k10 | 500 | 0.064649 | 0.300925 | 0.006294 | 0.005328 | 0.002593 | -0.004402 | 0.009810 | -0.006822 |
| mixed_gmm_label_skew_k10 | 1500 | 0.036260 | 0.265521 | 0.003131 | 0.001847 | 0.000984 | -0.006958 | 0.013470 | -0.006688 |
| mixed_gmm_label_skew_k10 | 5000 | 0.021818 | 0.190631 | 0.004051 | 0.001316 | -0.000487 | -0.007966 | 0.006430 | -0.004167 |
| mixed_gmm_label_skew_k10 | 15000 | 0.014229 | 0.232146 | 0.003521 | 0.000878 | 0.005894 | -0.005336 | 0.015530 | -0.005193 |

H_ref is an independent finite synthetic matrix. The same-target finite-H_ref excess uses the same released calibration vector b_cal and isolates synthetic-pilot fitting sensitivity conditional on finite H_ref. The validation LP instead uses real validation b_val and has greater access; its gap also includes a target difference. Neither LP is a population oracle. Fresh-sample primary differences are constrained minus size; negative favours constrained. Split seeds share Adult people and pilot replicates share fitted models.
