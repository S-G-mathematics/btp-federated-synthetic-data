# Weight methods and method-family claims

The experiment keeps a fixed family of generators and returns scalar weights
on the probability simplex. The eight named method families are:

| Family | Implementation or interface | Data access and interpretation |
|---|---|---|
| Predictive score | `pseudo_bma_logscore` | Softmax of summed common-reference predictive scores; temperature controls concentration. Uses supplied validation scores. |
| Predictive evidence BMA | `predictive_evidence_bma` | Normalizes summed common-reference scores plus a supplied model prior. This is conditional on the fixed fitted candidate models, not integrated training-model evidence. |
| Stacking | `stacking_logscore` | Maximizes the common-reference mixture log score. Requires supplied validation scores. |
| Moment calibration | `moment_l2` | Constrained least-squares matching of `H @ w` to `b`. |
| KMM | `kernel_mean_matching` | Calls the moment solver; caller must supply kernel mean embeddings in `H` and target embedding in `b`. This is a simplex-constrained squared embedding discrepancy. |
| Distributionally robust calibration | `robust_query_calibration` | Minimizes the worst query discrepancy plus variance-radius term. Inspired by uncertainty-set robustness; it is not a faithful implementation of the AFL paper. |
| Log-pool | `btp.operators.fit_operator('logpool', ...)` | Normalized geometric pooling restricted to a synthetic candidate support. A distinct aggregation operator, not a scalar linear-mixture rule. |
| Barycenter | `btp.operators.fit_operator('entropic_barycenter', ...)` | Finite empirical entropic transport with a declared mixed-data cost and a recorded finite weight search. Not the exact unregularized continuous barycenter. |

All score-based methods require common-reference `log_likelihood` values and
are marked privileged by default. Optional `settings["sample_weights"]` must
be finite, strictly positive, length `n`, and sum to `n`; defaults are unit
weights. This keeps score scale stable while allowing a target reference
population to reweight calibration rows. When calibration client proportions
differ from training mass `alpha`, construct row weights proportional to
`alpha_client / n_client_cal`, then scale them to sum to the number of
reference rows. Stacking uses a weighted sum of per-row mixture log scores;
pseudo-BMA and BMA use weighted sums of per-row model log scores. A nonuniform
weight vector makes BMA a power predictive-evidence calculation rather than an
ordinary Bayesian posterior update. The supplied scores must use the same
reference observations and scoring convention across candidates. Stacking and
predictive-evidence BMA necessarily use those scores; the moment, KMM,
robust-calibration, uniform, size, minimax, and GLS weight methods consume
summary features and do not need server raw records. `oracle_query_minimax`
labels an explicitly real-validation target supplied to the same query-minimax
optimizer and is therefore an oracle diagnostic.

The remaining implemented methods are supporting baselines, not additional
novelty claims: `uniform`, `size`, `query_minimax`, `oracle_query_minimax`,
`entropy_calibration`, and `uncertainty_gls`. GLS whitens feature residuals
using a covariance for the common residual estimand. It does not assign
inverse-variance weights to generators with different local truths.

The postpilot `target_budget_minimax` ablation constrains `||w-alpha||_1`
while minimizing the same fixed-pilot query maximum. Its declared grid and
release boundary are in `docs/TARGET_BUDGET_ABLATION.md`. It is a constrained
calibration variant, not an additional method-family novelty claim.

## Development selection correction (2026-10-24 UTC)
The earlier per-cell validation selector used unseen-interaction query MAE to break ties in primary query maximum. This contaminated the purported untouched audit role in tied cells. The corrected selector uses primary validation query maximum followed by deterministic method name only; the unseen interaction workload is audit-only. Historical outputs remain exploratory, with tie-bridge evidence in reports/selection_tiebreak_audit_20261024/.
