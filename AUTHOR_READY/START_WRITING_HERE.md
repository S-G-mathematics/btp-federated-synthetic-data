# Start writing here

**Status: `EXPERIMENTAL_WORK_COMPLETE_WITH_EXPLICIT_SCOPE_LIMITS` (25 October 2026).** The retained comparative thesis is ready for theory, interpretation and writing. No further experiment is required for that bounded thesis. This author pack is an editorial addendum to the immutable executable version-2 project archive; it does not contain code, raw datasets or model checkpoints.

## Research question and empirical answer

Under a fixed client-population target and an explicit release contract, can statistical aggregation improve the empirical fidelity of synthetic tabular data over properly tuned, schema-corrected sample-size weighting without unacceptable target-mass shift? The registered constrained weighting comparison did **not establish** its practical query-max gain of 0.005. Corrected Adult development had 0/18 practical-gain slices and mean constrained-minus-size difference **+0.002427903**; frozen Adult official-holdout scoring had 0/6 slices and mean difference **-0.000214907**. The Bank external dataset had 0/4 slices and mean difference **-0.001331749**. Negative values favour weighting. These results neither prove equivalence nor exclude smaller, workload-specific gains.

## Frozen procedure

- Non-neural local **Gaussian copula** with the frozen per-client train/local-tune grid, public schema and deterministic Adult education/education-number projection.
- Client target mass `alpha_i=n_i/sum_j n_j`; main synthesis weights **`w=alpha`**. Exactly 10,000 synthetic rows per draw, allocated by largest remainder; five draws per cell.
- Primary reference: alpha-standardized empirical held-out client query means. Ordinary pooled empirical answers are separate. Primary loss is the maximum absolute error over **152 registered queries**; 23 additional audit queries are secondary and were viewed during development.
- Three skews, `K=5/10`, confirmation seeds 404/505, size/uniform/constrained comparisons, registered conditional support gate and source-specific logistic/extra-trees calibration. The main pipeline is **nonprivate**.
- Immutable campaign freeze SHA256: `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`.

## All twelve packages

See `TWELVE_PACKAGE_ACCEPTANCE.md` for the question, exact evidence, result, scope, exclusion and status of each package. Eleven are `COMPLETE_BOUNDED_FINDING`; Experiment 3 is `CLOSED_NEGATIVE_OR_INAPPLICABLE` because regrouping mixtures of client-subset mixtures adds no expressive family.

## Five strongest supported findings

1. Constrained weighting did not meet the registered practical gain over size weighting in the Adult development, frozen Adult confirmation or frozen Bank replication matrices at their declared targets and workloads.
2. Fixed-pilot LP certificates describe only finite synthetic candidate matrices; pilot and synthetic sample size change sampling error without guaranteeing lower fresh-sample model error.
3. The frozen copula's female-conditional output has a severe measured sex/relationship dependency failure: `relationship=Husband` was zero in the alpha-standardized real female reference and 0.340–0.399 in generated female rows across all 12 confirmation cells; mean absolute error was 0.375 despite zero condition violations.
4. At the **registered unequal** training budgets, privileged real TRTR logistic probabilities had Brier 0.101987/AUROC 0.904646 versus synthetic-size TSTR 0.129818/0.856167 on the same official people. Real used 21,148/4,880/3,254 train/tune/calibration rows; synthetic used 10,000/2,000/2,000 generated rows.
5. The main released models and summaries are nonprivate; in three measured copula cells, model-plus-metadata application bytes exceeded comparably serialized raw client-table bytes. A separate conditional-DP histogram and adapted FLAIM reference do not protect the main pipeline.

## Five unsupported claims to avoid

1. A generally superior or novel weighting algorithm, equivalence of methods, or a population-TV guarantee.
2. Whole-pipeline differential privacy, secure cross-institution deployment or compression of raw tables.
3. Arbitrary-condition fidelity or a generalizing learned conditional sampler.
4. Intrinsic synthetic-versus-real utility inferiority at matched training size, or synthetic-over-real superiority.
5. Independent-person confirmation from overlapping Adult seeds or potentially repeated Bank contacts, or automatic publication novelty.

## Targets and access

For query `q`, the real empirical answer is `b_R(q)=sum_i alpha_i mean_{z in D_i^reference} q(z)`; the synthetic answer is `b_S(q)=m^{-1}sum_{z in D_S}q(z)`. The primary loss is `max_{q in Q_primary}|b_S(q)-b_R(q)|`, where `Q_primary` has 152 declared queries. This is measured between **existing real and generated datasets**, not unknown populations. Changing generator weights does not redefine `alpha`. F1-F3 real-row likelihood access was privileged; released-summary rules used only declared model/aggregate inputs; adapted FLAIM used a different interactive raw-client contract.

## Where to find the evidence

- `PAPER_TABLES/` contains editable saved and derived CSVs with a caption registry.
- `PAPER_FIGURES/` contains scientific figures, role-specific captions and vector exports where reproduced from saved tables.
- `CLAIM_TO_EVIDENCE.csv` maps retained claims to source artifacts and manuscript sections.
- `EMPIRICAL_METHODS_AND_RESULTS.tex` is typeset writing material; the PDF beside it is a rendered reading copy.
- `FINAL_SIGNOFF.md` records the editorial corrections and exclusions.
- Complete executable project on the laptop: `D:\dot\BTP_EC2_Complete_Handoff_20261024\BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip`, SHA256 `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf`.
- Supervisor documentation/results archive: `D:\dot\BTP_EC2_Complete_Handoff_20261024\BTP_SUPERVISOR_DOCS_AND_RESULTS_20261025.zip`, SHA256 `5424097489750f1621200369033ad456b86466436ba6250aafde57e7a01bd232`.

Historical protocol files can retain dated “locked” or “incomplete” language. The current state is this sign-off, the twelve-package register and the immutable freeze. The first **confirmation-scoring** read of official Adult test was after freeze; earlier raw-test integrity and duplicate checks did not score or select a method.
