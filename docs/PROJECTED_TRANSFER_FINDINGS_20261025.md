# Finite-query conditional transfer: six-cell development findings

**25 October 2026 local time.** The protocol in `docs/PROJECTED_TRANSFER_PROTOCOL_20261025.md` was fixed before this audit. Its elementary mathematical statement, proof and counterexample are in `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md`. The official Adult test and confirmation seeds 404/505 were not used.

## Execution and reproducibility

All six corrected projected development cells completed on EC2 under the shared one-worker lease: Chow-Liu age/K5 and mixed-GMM label-skew/K10, each seeds 101/202/303, with fixed size/constrained weights. The 30,000-row teacher mixture per method/cell was regenerated at the prior conditional-student seed. **Every teacher condition count, condition mass and real alpha mass matched** the saved prior conditional audit. There were no failure files; 79 tests passed. Each of four registered conditions has two weight routes per cell, giving 48 condition-bound rows. The 142 feature-only queries yield 6,816 teacher conditional answers; 36 supported route/condition/cell combinations yield 5,112 saved student/direct query triangles. Raw per-cell configurations and CSVs: `results/projected_transfer_20261025/`. Aggregates: `reports/projected_transfer_20261025/`; laptop copies: `reports/projected_transfer_local_20261025/`. Logs: `logs/projected_transfer_{initial,remaining,report}_20261025.log` and `logs/ec2_tests_projected_transfer_20261025.log`.

## Support and bound behavior

The deterministic finite-query ratio bound held in all 48 rows. The table shows three-split means under **size weighting**; constrained rows and per-seed values remain in `support_bound_summary.csv` and `all_condition_bounds.csv`.

| Family / condition | Mean real alpha mass | Mean observed conditional max | Mean empirical ratio bound | Operational support |
| --- | ---: | ---: | ---: | --- |
| Chow-Liu / age25-45 | 0.5461 | 0.0372 | 0.1261 | supported |
| Chow-Liu / Bachelors+age30-60 | 0.1137 | 0.1015 | 0.2383 | supported |
| Chow-Liu / female | 0.3268 | 0.1066 | 0.1396 | supported |
| Chow-Liu / rare doctorate+age60-90 | 0.00205 | 0.6124 | 0.8881 | **abstain** |
| Mixed GMM / age25-45 | 0.5451 | 0.0768 | 0.1166 | supported |
| Mixed GMM / Bachelors+age30-60 | 0.1121 | 0.1364 | 0.2415 | supported |
| Mixed GMM / female | 0.3285 | 0.3577 | 0.3798 | supported |
| Mixed GMM / rare doctorate+age60-90 | 0.00209 | 0.5339 | 0.9794 | **abstain** |

The rare condition had positive empirical teacher mass, so an algebraic conditional and bound can be computed, but it failed the prior 300-row/1% teacher support gate in every method/cell. It remains an operational abstention, not a successful conditional generator. Its pooled real assessment count could be as low as three. The denominator makes the bound loose or saturated near one. Conversely, GMM's female condition has substantial mass yet its conditional query maximum is large; support alone does not ensure fidelity. These are finite assessment/teacher results, not population quantities. Split seeds reuse Adult people.

## Separate student accounting

The saved matched-row independent direct-teacher and postfiltered trained-student answers satisfied the empirical triangle for all 5,112 feature-query rows. On age25-45, size-weighted mean absolute query error was 0.00609 direct versus 0.00849 student for Chow-Liu, and 0.00755 versus 0.00984 for mixed GMM. On Bachelors+age30-60 it was 0.01105 versus 0.01312 and 0.01279 versus 0.01490, respectively. These differences include finite draw noise and do not isolate a population student-training error. The direct-teacher rows are from an independent pool; the student route is additionally fitted and postfiltered. Rare-condition student/direct rows are absent by design. Full per-query accounting and condition-specific maxima are in `all_student_teacher_triangles.csv` and `student_direct_summary.csv`.

This strengthens bounded Experiment 11 support-dependent evidence but does not establish arbitrary-condition accuracy, universal predictive transfer or a new theorem. The elementary ratio statement only controls registered queries when **both** joint intersections and condition mass are measured, with positive support. The binary counterexample in the proposition shows that matching one-way queries alone permits complete conditional reversal. No fixed-target weighting benefit or official-test permission follows from this audit.
