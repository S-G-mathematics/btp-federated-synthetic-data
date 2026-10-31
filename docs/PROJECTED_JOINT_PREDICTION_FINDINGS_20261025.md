# Projected joint-implied income prediction findings — 25 October 2026 local time

## Execution and interpretation

The registered `docs/PROJECTED_JOINT_PREDICTION_PROTOCOL_20261025.md` ran on the existing EC2 under the shared heavy-compute lease, one worker and one native thread. It used the six fixed development cells (Chow-Liu age/K5 and mixed-GMM label-skew/K10, seeds101/202/303), their original projected local checkpoints and size/constrained weights. For each development-assessment feature row X, the evaluator scored both income labels under the mixture and normalized them. It compared the result with the previously trained/calibrated synthetic logistic and extra-trees predictors and privileged real-trained TRTR on **identical covered people**, with the fixed alpha-standardized global weights. No held-out real row entered model fitting or weight selection. Official Adult test and confirmation seeds404/505 remained locked.

All 6/6 cells completed without a failure file; the suite passed **79 tests**. Exact source row IDs, client IDs and labels were checked against immutable partition manifests and the prior paired predictions. Raw paired probabilities and per-client metrics are at `results/projected_joint_prediction_20261025/<cell>/`; aggregate tables at `reports/projected_joint_prediction_20261025/`, with laptop copies under `reports/projected_joint_prediction_local_20261025/`. Logs: `logs/projected_joint_prediction_initial_20261025.log`, `logs/projected_joint_prediction_remaining_20261025.log`, `logs/ec2_tests_projected_joint_prediction_20261025.log`.

The projected Chow-Liu local scores are exact probabilities **for their declared fitted discretized integer/categorical model**, including education-code pushforward. Mixed GMM uses approximate transformed continuous scores for rounded/clipped outputs; normalizing those scores gives an **approximate predictive route**, not an exact emitted-row conditional probability. Raw score magnitudes are not compared across families. Both routes assigned finite two-label mass to every observed development-assessment person in all six cells: alpha-weighted coverage was 1.0, with zero recorded off-support rows. This is observed-row coverage only; arbitrary new X may be off support, and the evaluator would abstain rather than smooth or fill it.

## Paired global predictive results

| Fixed family | Weights | Joint-implied AUROC | Synthetic logistic AUROC | Joint-implied Brier | Synthetic logistic Brier | Privileged TRTR logistic Brier |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Chow-Liu age/K5 (exact fitted joint) | Size | 0.843927 | 0.836700 | 0.128481 | 0.137953 | 0.109576 |
| Chow-Liu age/K5 (exact fitted joint) | Constrained | 0.843437 | 0.840781 | 0.128540 | 0.136221 | 0.109576 |
| Mixed GMM label-skew/K10 (approximate score) | Size | 0.861302 | 0.884271 | 0.126214 | 0.116265 | 0.108153 |
| Mixed GMM label-skew/K10 (approximate score) | Constrained | 0.861201 | 0.884977 | 0.130553 | 0.118031 | 0.108153 |

The exact Chow-Liu joint route had a lower mean Brier score than synthetic logistic in each of the three age split seeds under both weight rules, but still trailed privileged TRTR. Its AUROC advantage over synthetic logistic was not uniform by seed. The approximate GMM joint route had a worse Brier score and lower AUROC than synthetic logistic in every reported label-skew seed under both weight rules. Constrained weights did not materially improve the joint route here; in GMM they raised mean joint Brier from 0.126214 to 0.130553. Full AUPRC, log loss, ECE, extra-trees comparisons, per-client metrics and paired seed differences are retained in CSVs. These three Adult splits overlap in people and are not independent cohorts.

This bounded Exp7 result separates a model-implied conditional distribution from a separately trained predictor. It does not prove conditional correctness from joint query fidelity, does not validate the approximate GMM score as exact probability mass, and does not establish a globally superior generator or weighting rule. It supports the current draft finding that no practical fixed-target weighting improvement has been established; official confirmation remains gated on a campaign-wide procedure freeze.
