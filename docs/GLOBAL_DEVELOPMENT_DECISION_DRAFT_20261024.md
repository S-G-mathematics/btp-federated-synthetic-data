# Draft campaign-wide development decision — 24 October 2026 UTC

**Status: exploratory development decision, not `SELECTION_FROZEN.json`. Official Adult test remains locked.** This memo records what the completed evidence supports and which procedure details are still unfrozen. It must not be presented as independent confirmation or a sign-off for publication.

## Declared question and target

Under the fixed training client masses `alpha_i=n_i/sum(n_i)` and the nonprivate released-model/aggregate-summary contract, does a weighting rule lower the alpha-standardized empirical development-assessment primary query maximum by at least **0.005** versus tuned projected sample-size weighting, while satisfying `||w-alpha||_1<=0.25`, `w_i>=0.5 alpha_i`, the audit query guardrail, supported subgroup tolerance and synthetic AUROC noninferiority? The ordinary pooled held-out dataset is a separately labeled secondary reference. Adult `fnlwgt` remains a feature. All results concern finite Adult datasets/workloads, not population TV.

## Alternatives and evidence actually considered

| Procedure | Development evidence | Decision for fixed-target use |
| --- | --- | --- |
| Projected size weighting | Mandatory baseline across corrected 54-cell core, all secondary selected cells, sample/pilot sensitivity and conditional checks | **Provisional fallback**; no improvement claim |
| Fixed constrained query-minimax (`L1<=0.25`, floor `0.5alpha`) | Corrected 54-cell core: mean paired primary difference **+0.002428**, 0/18 three-seed slices with practical mean gain; three individual GMM cells reached the margin | No practical aggregate improvement established |
| Per-cell validation-selected release-only rule | 28/54 assessment cell wins, mean difference −0.000458; only one practical three-seed slice, but mean weight L1 shift **1.222** | Excluded from fixed-target selection by representation budget; not a global method |
| Privileged score families F1–F3 | Per-record real calibration scores within evaluator | Cannot establish equal-access deployable advantage; not a candidate under the stated release-only contract |
| Finite logpool/entropic barycenter | Fixed support/best-found operator comparators | Different operators with limited support/optimization; no global oracle claim or demonstrated compliant winner |

The six selected secondary cells were chosen **after** the primary matrix and are exploratory. Chow-Liu age/K5 constrained weights worsened primary mean by +0.004626 and supported-subgroup max error by +0.015095, failing its +0.01 tolerance despite AUROC gains. Mixed-GMM label-skew/K10 improved primary mean only −0.001746 (short of −0.005) and subgroup max error −0.009256, with essentially neutral AUROC. At m=40,000, both selected families' constrained primary differences were adverse (+0.006713/+0.001492). Repeated pilots up to 15,000 rows/client reduced finite-H error and same-target LP excess but gave no practical three-seed mean D_S gain. The registered-condition student generally underperformed direct rejection for age/conjunctions; the rare condition abstained. These checks strengthen a **negative comparative finding**, not statistical equivalence or proof that weighting never helps.

The separate public zero-atom histogram offers a matched conditional DP baseline only for individual fresh-noise releases under fixed public membership/size; its nonprivate primary error remains ~0.33. The projected model/summary pipeline and full research bundle are nonprivate. Serialized disk-byte inventory is complete, actual network traffic is not measured. No FLAIM/Private-PGM or external-dataset replication has run.

## Current decision

**No improved fixed-target weighting method has been established in development. Retain tuned projected size weighting as the default comparator.** Keep all null/adverse cells and the initial failed/historical runs. The three split seeds reuse Adult people; five synthetic draws measure generation variation, not independent cohorts. Do not claim novel weighting superiority, synthetic-over-real predictive superiority, full-pipeline DP, arbitrary conditional generalization, population oracle optimality, or publication readiness.

## Why this is not the official-test freeze

The campaign has not frozen a **single global generator and local tuning rule**, application-specific conditional support policy for arbitrary requests, final workload/utility trade-off across every viable global candidate, or a fully specified confirmation procedure. Assessment outcomes have already informed exploratory extensions. A complete `SELECTION_FROZEN.json` would need the selected procedure and registered baselines, code/config/dataset/split hashes, selection metric and validation-only decision rule, exact sample budgets/seeds, support/abstention and release contract, timestamp, alternatives and `test_used_for_selection:false`. Official Adult test and confirmation seeds404/505 must remain unopened until that written global freeze. They will still reuse Adult people; an external dataset is needed for broad transfer claims.

Next executable research work: complete a validation-only global generator/procedure decision or explicitly close the thesis as a comparative negative study; record the remaining twelve-package limitations, obtain a matched external/closest-prior-art baseline if time permits, and seek supervisor review of the freeze memo before optional confirmation. This document is a dated draft decision, not that freeze.

## Development addendum (25 October 2026 local time)

A fixed six-cell query audit reproduced all prior primary maxima and saved every primary/unseen answer. It found a primary alpha-versus-unweighted-pooled target gap up to 0.009984; common two-way GMM mean absolute error worsened under constrained weighting despite a small mean primary-max gain. A separate fixed six-cell conditional-transfer audit checked 48 finite-query empirical ratio bounds and 5,112 student/direct triangles; the rare condition remained 12 operational abstentions, while a high-support GMM female condition still had large error. The ratio fact has an elementary proof and a counterexample to universal transfer from incomplete query lists. See `docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md`, `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md` and `docs/PROJECTED_TRANSFER_FINDINGS_20261025.md`. Neither addendum changes the draft decision or opens the official test.
