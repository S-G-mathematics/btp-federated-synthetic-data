# Adult education-code repair versus weighting: postpilot ablation

**Date:** 24 October 2026 UTC. **Status:** exploratory development finding after inspecting the 54-cell core. This is neither a preregistered primary comparison nor official-test confirmation.

## Problem discovered

The official Adult development TRAIN rows show a deterministic education-category to education-number code relationship: the evaluator measured zero mismatches in TRAIN across the audited split seeds. A size-weighted 10,000-row sample from the saved local checkpoints violated that relation in about 25.4% of Chow-Liu rows, 77.6% of copula rows and 61.2% of mixed-GMM rows on average across the 18 cells per generator. All sampled numeric fields were integer-valid. Mean capital-gain zero-frequency errors were around -0.006 to -0.008 and capital-loss zero-frequency errors around -0.001 to -0.003, smaller than the relation defect. Evidence: reports/structural_features_20261024/cell_diagnostics.csv and slice_summary.csv; code: scripts/audit_structural_features.py.

The existing primary query workload contains education-number marginal thresholds, but no direct education/education-number relationship query. The registered unseen-interaction audit workload also lacks that relationship. This structural issue was therefore not fully visible in the prior query metrics. A relation-mismatch rate is now reported as a **postpilot structural diagnostic**, not retroactively inserted into the frozen earlier workload.

## Matched ablation and preserved failure

scripts/education_projection_ablation.py declares a fixed Adult education-to-number map and verifies it against development TRAIN only. For each of the 54 core cells, it loads the same local checkpoints and saved size/constrained weights, draws exactly 10,000 rows using five matching seeds per method, and evaluates each draw before and after setting education-number to the declared code of its education category. The real comparison remains alpha-standardized development assessment. The mapping is a postpilot proposed public support rule, not a real-test-fitted statistic or a privacy mechanism. No projected joint log-score is claimed; the model's old score refers to unprojected rows.

The first version failed on education='?' samples because the map has no code for that explicit missing category. Its failure is retained in results/education_projection_ablation_20261024/. The corrected run retains such rows unprojected and counts them unsupported; it does not fabricate a code. The completed outputs are in results/education_projection_ablation_fixed_20261024/, with paired CSVs/plot in reports/education_projection_20261024/. All 54 cells completed with 20 matched method/projection/replicate rows per cell.

| Generator | Raw size education mismatch | Mapped size mismatch | Raw size query max | Mapped size query max | Constrained minus size query max **after** mapping |
|---|---:|---:|---:|---:|---:|
| Chow-Liu | 0.25400 | 0.00139 | 0.09730 | 0.02850 | +0.00922 |
| Copula | 0.77576 | 0.00031 | 0.02690 | 0.02687 | +0.00253 |
| Mixed GMM | 0.61236 | 0.00102 | 0.06190 | 0.05208 | +0.00234 |

Table entries are means across 18 development cells per generator, each with five synthetic draws. Positive constrained-minus-size means the constrained rule is worse. For Chow-Liu, mapping improves size query maximum by mean -0.06880; for mixed GMM by -0.00983; for copula by about -0.00003. Before mapping, the constrained rule had mean differences -0.01598 for Chow-Liu, +0.00266 for copula and -0.00217 for GMM. After mapping, those differences become +0.00922, +0.00253 and +0.00234. **No generator/partition/K slice has a mean post-mapping constrained gain of at least 0.005.** At cell level, the constrained rule still has a lower primary maximum in 21/54 cells, which is not a practical-margin or global-selection result.

The registered unseen audit query maximum is unchanged by this projection in every cell because that workload has no education-number query. This is a measurement blind spot, not evidence that the education relationship is unimportant. The remaining mapped mismatch is exactly the unsupported '?' education rate (generator means about 0.00139, 0.00031 and 0.00102). Per-slice and per-cell effects, including audit values and synthetic seeds, are in reports/education_projection_20261024/slice_effects.csv and paired_cell_effects.csv.

## Interpretation and required follow-through

The earlier large Chow-Liu weighting gains cannot be interpreted as durable evidence that reweighting fixes heterogeneous aggregation: a simple train-verified support projection improves size weighting more and removes the mean constrained advantage in these development cells. This is a concrete generator-error-versus-weighting result. It is **not yet a deployable or confirmatory result**: the map was introduced after examining development failures, and the score-based routes still describe unprojected local model outputs.

Before any global freeze, either declare the education map as public structural schema and implement it consistently for every generator/method, with its effect on exact/approximate scoring and release bytes documented, or keep it as an evaluator-only oracle repair and reject support-invalid routes. A revised prospective workload should include the education-code consistency query and relevant held-out dependencies. Utility, subgroup, conditional, privacy and resource comparisons need to be repeated for the repaired route and tuned size baseline. Official Adult test remains locked.
