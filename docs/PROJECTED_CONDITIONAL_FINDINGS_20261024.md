# Projected registered-condition development findings — 24 October 2026 UTC

## Execution and boundaries

The corrected conditional audit ran all six fixed projected development cells: Chow-Liu age/K5 and mixed-GMM label-skew/K10 at seeds101/202/303, size and fixed constrained weights. Each method/cell used a 30,000-row released-model teacher pool to train per-registered-condition projected Chow-Liu feature estimators and a **separate 30,000-row teacher pool** for direct rejection. Student and direct routes were evaluated on exactly the same number of accepted rows within a method/condition/cell, up to 2,000. All 6/6 corrected cells completed, with zero failure files and 76 passing tests. Per-cell wall time was 13.50–15.47 seconds. The official Adult test and confirmation seeds404/505 were not evaluated.

Raw evidence: `results/projected_conditionals_v2_20261024/<cell>/` contains condition metrics, all query answers, accepted student samples, trained model checkpoints, settings and hashes. Aggregates: `reports/projected_conditionals_v2_20261024/` (also copied to laptop `reports/projected_conditionals_local_20261024/`), including an audit of 36 saved supported student samples: **zero postfilter condition violations and zero mapped education-code violations**. Logs: `logs/projected_conditionals_v2_initial_20261024.log`, `logs/projected_conditionals_v2_remaining_20261024.log`, `logs/ec2_tests_projected_conditionals_20261024.log`. The first one-cell version used unequal route row counts and is preserved under `results/projected_conditionals_20261024/` as historical, excluded from this comparison. An initial report-only type error while auditing saved samples was corrected; cell data were not changed.

## Matched within-condition feature-query error

| Family / condition | Size direct mean max error | Size trained-student mean max error | Constrained direct mean max error | Constrained trained-student mean max error |
| --- | ---: | ---: | ---: | ---: |
| Chow-Liu age/K5 / age25–45 | 0.036158 | 0.069892 | 0.040319 | 0.065937 |
| Chow-Liu age/K5 / female | 0.110975 | 0.112472 | 0.110433 | 0.106760 |
| Chow-Liu age/K5 / Bachelors+age30–60 | 0.104870 | 0.136704 | 0.119548 | 0.142656 |
| GMM label-skew/K10 / age25–45 | 0.084292 | 0.121190 | 0.065541 | 0.137889 |
| GMM label-skew/K10 / female | 0.369236 | 0.354045 | 0.352127 | 0.346956 |
| GMM label-skew/K10 / Bachelors+age30–60 | 0.146748 | 0.193057 | 0.145561 | 0.195674 |

These are three-seed development means; split seeds reuse Adult people. Lower error is better. Direct teacher rejection beat the trained student for the age and age+education conditions in every family/weight mean. The student was slightly better for the female condition in some cells, especially the GMM size route, but absolute error there remained large. For age and age+education conditions, raw student condition violations averaged roughly **20–24%** before filtering, so only around 1,500–1,600 of the requested 2,000 rows were usable. Female raw violations were about 0.1–0.2%. The comparison matched final row counts; the training teacher pool is an upfront cost for the student, while direct rejection from a joint model incurs condition-dependent acceptance cost. This study does not establish a net speed advantage for either across repeated requests.

The `rare_doctorate_age60-90` condition failed the predeclared synthetic teacher support gate for **both weights in all six cells**; there are 12 explicit abstentions and no fabricated conditional success. Its real development-assessment count was as low as three people. Other three conditions were supported in all cells. Support decisions used synthetic teacher counts only; real held-out counts were evaluator diagnostics.

The student was trained separately for each registered condition, so **cross-condition generalization and arbitrary condition requests remain untested**. The result is a bounded Exp5 development audit, not completion of every conditional-generation requirement. It gives no reason to prefer constrained weighting globally, and it does not override the fixed-target primary fidelity failure. The projected models and released unnoised summaries remain nonprivate. No campaign-wide freeze, official-test confirmation or broad conditional-sampler claim follows.
