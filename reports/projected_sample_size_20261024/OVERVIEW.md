# Projected sample-size development audit

Six fixed-model cells; five draws at each m. The 10,000-row observations were reused exactly from the compatible constrained audit. Official Adult test was not evaluated.

| family | m | size_query_mean | size_query_draw_range_mean | constrained_query_mean | delta_query_mean | delta_query_min_seed | delta_query_max_seed | delta_unseen_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chow_liu_age_k5 | 2500 | 0.030461 | 0.009476 | 0.037755 | 0.007294 | 0.002105 | 0.011498 | 0.003642 |
| chow_liu_age_k5 | 10000 | 0.028363 | 0.004746 | 0.032989 | 0.004626 | -0.002485 | 0.009712 | 0.004497 |
| chow_liu_age_k5 | 40000 | 0.027961 | 0.002542 | 0.034673 | 0.006713 | 0.000510 | 0.010788 | 0.004863 |
| mixed_gmm_label_skew_k10 | 2500 | 0.051413 | 0.015467 | 0.055364 | 0.003952 | -0.009958 | 0.012562 | -0.007868 |
| mixed_gmm_label_skew_k10 | 10000 | 0.055305 | 0.011305 | 0.053559 | -0.001746 | -0.006546 | 0.006470 | -0.008839 |
| mixed_gmm_label_skew_k10 | 40000 | 0.051658 | 0.003472 | 0.053149 | 0.001492 | -0.007119 | 0.013830 | -0.008501 |

Negative constrained-minus-size differences favour constrained weighting. The three split seeds reuse Adult people. Draw ranges capture synthetic sampling variation only. Different m values use the same public seeds and can share random-stream prefixes; they are not independent replication units. The real reference is finite and is not population truth.
