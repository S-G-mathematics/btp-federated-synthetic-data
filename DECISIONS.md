# Decisions and rationale

- Latest non-neural statistical framework supersedes the original neural shared/private-head proposal.
- Empirical real D_R vs synthetic D_S is the measured fidelity object. Fixed target alpha is not changed to flatter a weight method.
- Preserve official test. Quarantine exact training duplicates and keep other duplicate groups together.
- Fixed public schema/vocabulary provides comparable support and avoids hidden pooled/test preprocessing.
- Local tune, permitted calibration summaries, privileged validation oracle, and final test have separate roles.
- F1/F2/F3 score-based comparisons are privileged unless a separate client-side score protocol is implemented and accounted for.
- Eight families are not eight innovations; extra scalar solvers are supporting baselines. Conditional fixed-model BMA/pseudo-BMA can be equivalent.
- Pure client-subset mixtures are algebraically equivalent to a single mixture. Different aggregation operators need own-family comparators.
- Finite-support geometric/transport adapters are explicit approximations and have diversity/support ceilings.
- Strong model fitting uses training/tune data, multiple settings/initializations and validation diagnostics; no promise of an artificially close reconstruction.
- DP noise is freshly drawn from private OS entropy. Exposed deterministic noise seeds are marked research-only, not DP-eligible. Public sampling seeds are allowed postprocessing.
- Heavy full-data work belongs on the existing EC2 in an isolated namespace; bounded one-lane scheduling preserves other projects.
- Method selection uses development validation only. Completing smoke scripts is not completing the scientific work packages or establishing publishability.

## EC2 execution update ? 2026-10-24 UTC

- Use `/home/ubuntu/research-director/btp-federated-statistics-20261024/` as the isolated EC2 namespace, preserving the transferred ZIP and original SHA manifest.
- Keep new EC2 smoke and pilot outputs in separate result roots; do not describe bundled local smoke as EC2 work.
- Detect EC2 for the heavy scheduler from readable DMI vendor/product fields. The prior UUID read failed with `PermissionError` as unprivileged `ubuntu`.
- Apply the RP1 airbag skill as a BTP-specific audit workflow. The EC2-hosted read-only Luna worker was blocked by bubblewrap; do not claim its review completed or relax its sandbox just to satisfy a worker count.

## Six-generator and Genuity decisions (2026-10-24 UTC)
- Add compressed prototype KDE and exact discretized latent class as additional
  non-neural families. Keep their score kinds and release limits explicit.
- Treat first added-generator pilot results as diagnostic; prototype KDE
  exhibits large age/hours marginal discrepancies, and both candidates can
  concentrate weights on only two clients. A lower query maximum alone does
  not settle target representation or method selection.
- Keep published Genuity in a separate EC2 environment and transfer only the
  user-authorized token from D:. Local Genuity code stays on D:.
- Do not run or claim a Genuity comparison until its signed license activates.
  The available token did not verify, and the other catalogued keys expired.

## Genuity signed-key and comparator resolution (2026-10-24 UTC)
- The user explicitly authorized a replacement license. Use the local Genuity
  signing tool/key on D:, with the already documented expiry; transfer only
  the signed token to private EC2 storage. Published wheel activation passed.
- Genuity KDE and copula are sample-only client-private comparators, not
  released local joint models for the eight BTP weighting families.
- Retain Genuity KDE's severe structural-zero failure; do not clip/relabel it
  into apparent success. The copula's fractional Adult numerics require a
  separately declared public rounding projection and preprojection diagnostics.

## Stacking solver repair (2026-10-24 UTC)
- Preserve initial K=10/label-skew stacking failures as failed fits.
- Optimize normalized mixture log score with an analytic gradient and verify
  the concave objective's first-order dual gap. Use monotone EM only as a
  documented fallback with the same certificate; never relabel the original
  failed runs. Three saved-cell replays converged with gap < 1e-6.
- Rerun the complete K=10 grid under a new code hash for consistent corrected
  method comparisons, then reconsider development replication.

## Full-data twelve-stage pilot and conditional support correction (2026-10-24 UTC)
- The age/K=5/copula pilot executed all twelve starter stages on full Adult
  development splits. This is one measured cell, not completion of the broad
  scientific packages; `docs/WORK_PACKAGE_AUDIT.md` lists remaining work.
- The rare doctorate/older-age condition had 81 teacher rows and three real
  assessment matches but was marked complete with poor conditional fidelity.
  A support policy based only on teacher rows and teacher mass now controls
  abstention before held-out reference evaluation. Pilot thresholds are 300
  teacher rows and 1% mass. The change is postpilot development and must be
  validated on later seeds; seed101 is not independent confirmation.
- The public-bin nonprivate histogram and DP variants all had large query
  error because broad numeric bins lost zero atoms. Retain this matched
  negative result; do not infer DP noise was the dominant cause.

## Bounded replication checkpoint (2026-10-24 UTC)
- Stop heavy EC2 work after the seed202/303 copula replication campaign and
  save reports; the existing resource allowance does not specify an hourly
  dollar rate or authorize new spend. No official test has been scored.
- On 12 copula development cells, the within-cell validation choice beat
  size on assessment only 3 times; mean difference was +0.00018 query max
  error. Treat this as a preliminary null result, not a global method choice.
  Split seeds reuse the same Adult source records, so their cohort errors are
  correlated. No external-dataset generalization claim is made.
- The next bounded work is to complete current-code seed101 copula parity,
  replicate other viable generators, compare utility/conditional/privacy
  trade-offs, then freeze globally from development validation only.

## Current-code copula three-seed checkpoint (2026-10-24 UTC)
- Fill seed101 across all six partition/K cells under the same code hash as seeds202/303 before combining split-seed summaries. All 18 Exp 1/2 cells now have successful method rows and certified fixed-pilot oracle LPs.
- The within-cell validation choice beat the fixed size baseline on development assessment in 6/18 cells; average difference was +0.001348 query max error. This is exploratory and partly postpilot. Keep the size baseline viable and do not freeze a global winner or score official test.
- Preserve one-worker shared-lease scheduling and defer broader sweeps until the other active EC2 research loads allow them.

## Chow-Liu/GMM bounded development replication (2026-10-24 UTC)
- After the copula preliminary null, test whether size-weighting competitiveness depends on the local model family. Run Chow-Liu and mixed GMM for age, K=5/10, seeds202/303, one shared lane and three synthetic repeats. All eight Exp 1/2 cells and fixed-pilot LPs succeeded.
- The within-cell validation choice beat size on development assessment in 7/8 cells, average query max difference -0.017346. This contrast with copula is a development signal, not a global ranking: only age was replicated, splits overlap, and assessments are not official-test confirmation. Continue other skew cells and utility/privacy/representation trade-offs before any freeze.

## Supervisor-directed target and audit correction (2026-10-24 UTC)
- Primary D_R is alpha-standardized empirical held-out client data, with alpha from training mass. Ordinary pooled held-out counts are a separately labeled secondary reference; Adult fnlwgt stays a feature. The primary paired comparison is method-minus-size query maximum on the fixed public workload.
- The unseen-interaction workload was improperly used to break primary-score ties in the old per-cell selector. Correct it to primary query maximum then deterministic method name. Preserve historical outputs, use a 26-cell per-method Exp1/2 bridge and rerun 12 incompatible seed101 Chow-Liu/GMM cells. Old selected downstream stages are not bridgeable.
- Before analyzing new skew cells, register provisional representation limits L1(w,alpha)<=0.25 and w_i>=0.5 alpha_i, a 0.005 absolute practical query-gain margin, an unseen-audit deterioration guardrail of 0.005, and matched synthetic AUROC noninferiority tolerance of 0.01. These are application decision margins, not statistical significance or privacy guarantees. Five independent synthetic draws are required for final development comparisons.
- Keep official Adult test locked. If weighting fails the prospective guardrails, size weighting is an acceptable outcome.

## Generator repair before weighting claims (2026-10-24 UTC)
- The 54-cell raw core showed only four fixed-constrained slices clearing both the registered primary margin and development audit screen. A subsequent TRAIN-verified education-code projection is explicitly postpilot and exposed a severe structural defect invisible to the unseen audit workload.
- Do not interpret raw Chow-Liu weighting gains as method superiority: on the same five-draw samples, projecting education-number reduced mean size query maximum 0.09730 to 0.02850, and no projected generator/partition/K slice retained a 0.005 constrained-weighting gain. Preserve the first projection failure on education=? and count unmapped rows; do not fabricate codes.
- The mapping must be made an explicit public support rule or permitted release, with projected-score limitations and bytes documented, before a prospective repaired pipeline. Until then it is an evaluator postpilot ablation. The registered audit has been used as a development guardrail and cannot serve as independent confirmation. Keep size weighting viable and official test locked.

## Projected-model component boundary (2026-10-24 UTC)
- Declare the education-code map in the public schema and implement a wrapper that projects generated rows. For exact discretized local models, score projected rows by summing raw integer mass over the original education-number support. Keep copula/GMM scores approximate. Unit tests cover exact normalization, off-map zero mass, unknown-category identity and sampling; 73 tests pass including the version 2 workload check.
- This wrapper is not yet installed in local tuning, pilots, score matrices, operators or the campaign release ledger. Preserve old raw results and the postpilot mapped ablation as separate evidence; no projected-campaign success or privacy claim follows from unit tests.

## Version 2 integrated pilot (2026-10-24 UTC)
- Add a separate `projected_pilot` profile so local tuning, pilot summaries, released checkpoints and privileged score matrices consistently use projected model outputs. Add the postpilot education relation query as version 2. Keep historical raw cells and version 1 workload untouched.
- The first full-data Chow-Liu age/K5/seed101 development cell ran successfully, but its within-cell validation-selected kernel mean matching was worse than size by +0.006134 assessment primary query maximum. This is one cell, not a global verdict. Continue matched projected development comparisons; do not open official test or freeze from this outcome.

## Corrected projected matrix and fixed-target fallback (2026-10-24 UTC)
- Correct Chow-Liu's process-hash-dependent sampling order before matched comparisons. Preserve the first five projected cells as historical and rerun all affected cells in a distinct code-hash root. A subprocess regression test across two hash seeds passed; the final suite has 74 tests.
- Complete the projected version 2 Exp1/2 core across three generators, three partitions, K5/10 and seeds101/202/303, with five synthetic draws per method. The fixed constrained rule has no three-seed slice with a mean practical gain of 0.005 over tuned size, and its overall mean paired difference is +0.002428. One validation-selected mixed-GMM label-skew K10 slice has mean gain -0.006951 but mean L1 client-mass shift 1.222, violating the registered 0.25 budget. This is a development screen, not a global freeze or confirmation. Size remains the fallback while subgroup/utility/support/privacy/resource gates are incomplete.
- Keep the standalone public-bin histogram's DP claim separate. The projected model releases and unnoised summaries remain nonprivate, and the official Adult test stays locked.

## Projected secondary gate after the primary matrix (2026-10-24 UTC)
- Register the six-cell subgroup/utility protocol before inspecting its results: Chow-Liu age/K5 and mixed-GMM label-skew/K10 at seeds101/202/303, size versus fixed constrained weights, five subgroup draws, two tuned/calibrated learners, and separate privileged TRTR. Keep source row IDs and alpha-weighted development-assessment metrics.
- The six EC2 cells all completed and the suite passed 76 tests. Chow-Liu age constrained weights improved learner AUROC but worsened primary query max and broke the +0.01 supported-subgroup error guardrail. Mixed-GMM label skew passed subgroup and AUROC guardrails but its primary gain was only -0.001746, short of the -0.005 practical margin. Therefore neither becomes a global winner. Size remains the provisional fixed-target fallback; no official test or campaign-wide freeze is authorized by these development results alone. Evidence: `docs/PROJECTED_SECONDARY_FINDINGS_20261024.md`.

## Projected sample-size sensitivity (2026-10-24 UTC)
- Register m=2,500/10,000/40,000 and five public-seed draws for the same six fixed-checkpoint cells. Verify compatibility and reuse the prior 10,000-row draws exactly. The six EC2 cells completed under the shared lease with no failures; the suite remained at 76 tests.
- Draw-to-draw range fell as m grew, but at 40,000 rows constrained-minus-size mean primary query max was +0.006713 Chow-Liu age/K5 and +0.001492 mixed-GMM label-skew/K10. Neither family reached the practical -0.005 gain at any tested m. Retain tuned size as provisional fallback; do not reinterpret m-level draws or overlapping Adult split seeds as independent populations. Evidence: `docs/PROJECTED_SAMPLE_SIZE_FINDINGS_20261024.md`.

## Serialized release ledger (2026-10-24 UTC)
- Inventory file sizes for all 54 projected core cells and classify the access boundary. Client checkpoints total 45,838,513 serialized bytes and aggregate unnoised summaries total 8,668,152 bytes. These are disk artifacts from a single-process simulation, not actual network messages. No full-pipeline DP or communication-byte claim is justified. The privileged score track and evaluator-only manifests remain separate. Evidence: `docs/PROJECTED_RELEASE_LEDGER_20261024.md`.

## Repeated finite synthetic-pilot sensitivity (2026-10-24 UTC)
- Before results, register six fixed projected development cells, four pilot sizes (500/1,500/5,000/15,000 per client), five seeds, disjoint finite H_ref, exact source-H reproduction and fresh paired D_S. Preserve the initial tuple/list workload comparison failure separately; the corrected root completed all six cells, with 76 tests passing.
- Compare constrained vectors with a same-target LP on finite H_ref and the same released calibration vector b_cal to isolate synthetic-pilot fitting sensitivity. Its mean excess fell below 0.001 at 15,000 rows/client in both families. A separate privileged b_val LP has different access and cannot be called pure pilot uncertainty. Fresh D_S constrained-minus-size mean never reached -0.005 for either family at any registered pilot size. Tuned size remains provisional fallback, without global freeze or official test. Evidence: `docs/PROJECTED_PILOT_SENSITIVITY_FINDINGS_20261024.md`.

## Registered-condition student versus direct teacher (2026-10-24 UTC)
- Keep the first one-cell conditional result as historical after finding unequal route evaluation row counts. Rerun six cells with an independent direct-teacher pool and exactly matched accepted row counts, retaining the same synthetic support gate. The corrected run completed 6/6 cells with 76 tests passing; 12 rare-condition method-cells explicitly abstained and 36 saved supported student samples had zero postfilter/schema violations.
- The per-condition Chow-Liu student generally worsened within-condition query maximum for age and age+education relative to direct teacher rejection, with about 20–24% raw condition violations before filtering; limited female-condition improvements do not establish a general benefit. Do not claim arbitrary or unseen-condition generalization from separately fitted registered-condition students. Evidence: `docs/PROJECTED_CONDITIONAL_FINDINGS_20261024.md`.

## Versioned zero-atom privacy baseline (2026-10-24 UTC)
- Keep the original public-bin histogram as historical software evidence. Add a separate standalone histogram with fixed public capital-gain/loss zero atoms and public education-code projection, leaving the projected model code hash/checkpoints unchanged. Fit matched nonprivate and epsilon 1/4/8 private versions from the same six development client partitions, with five synthetic draws each. Fresh OS entropy is used for noise; no noise seed is serialized. The 78-test suite passes.
- The combined structural bridge changes both zero atoms and education projection: legacy nonprivate query max averaged about 0.953 versus corrected nonprivate about 0.333 on the same cells/seeds; do not attribute the whole reduction to a single repair. The corrected independent histogram still has large dependency error, and a single conditional DP histogram release does not protect the nonprivate campaign or raw ZIP. Three epsilon releases on one client compose to epsilon 13 under the fixed public membership/size assumptions; cross-seed/accounting boundaries remain open. Membership AUC is diagnostic, not proof. Evidence: `docs/PUBLIC_ATOM_PRIVACY_FINDINGS_20261024.md`.

## Draft global development decision (2026-10-24 UTC)
- Record “no improved fixed-target weighting method established” from the corrected 54-cell primary matrix and bounded secondary/sample/pilot/conditional/privacy checks. Retain tuned size as provisional fallback, not as a proof of optimality. This dated draft is **not** a campaign-wide `SELECTION_FROZEN.json`: global generator/procedure and complete confirmation policy remain unfrozen. Do not open official Adult test or confirmation seeds404/505. Evidence: `docs/GLOBAL_DEVELOPMENT_DECISION_DRAFT_20261024.md`.

## Same-person joint-implied income check (2026-10-25 local time)
- Score both income labels under each fixed projected mixture on the same development-assessment people as the calibrated synthetic predictors. Mark Chow-Liu's declared discrete joint route exact and mixed GMM's rounded/clipped score route approximate; abstain if both labels have zero mass. All six cells had 100% observed-row coverage and no failed score, with 79 tests passing.
- Chow-Liu joint-implied Brier improved over separately trained synthetic logistic on the selected age cells, but privileged TRTR remained better. Approximate GMM joint route had worse Brier/AUROC than synthetic logistic on selected label-skew cells. This is a bounded Exp7 finding, not arbitrary-X support or a globally superior weighting method. Evidence: `docs/PROJECTED_JOINT_PREDICTION_FINDINGS_20261025.md`.

## Fixed-query development audit (2026-10-25 local time)
- Keep the alpha-standardized client reference as the primary target, with pooled held-out answers explicitly secondary. Regenerate five fixed 10,000-row draws in six registered cells and reject any failure to reproduce prior primary maxima. All six passed, 79 tests passed, and every query-level answer was saved.
- The constrained-minus-size primary max was +0.004626 for Chow-Liu age/K5 and -0.001746 for GMM label-skew/K10. The latter misses the -0.005 practical margin and worsens common two-way mean absolute error by 0.016319. A conditional simultaneous 175-query radius is only an assumption-based calculation, not validated Adult uncertainty. Retain size as provisional fixed-target fallback; do not promote the viewed audit workload to independent confirmation. Evidence: `docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md`.

## Finite-query conditional transfer (2026-10-25 local time)
- Reconstruct the earlier 30,000-row teacher mixtures with exactly matching condition counts/masses in six fixed cells. The elementary ratio bound holds in all 48 empirical condition rows; its rare-support rows can be calculated but remain 12 operational abstentions. The student/direct empirical triangle holds on all 5,112 supported query rows, with separate fitted-student error and sampling effects unidentifiable from this identity alone.
- Document the proof and binary counterexample showing that matching an incomplete one-way workload does not guarantee a conditional or predictor. Treat the observed bound as finite-query algebra, not population TV, a universal guarantee or a novel theorem. The size fallback and official-test lock remain unchanged. Evidence: `docs/PROJECTED_TRANSFER_FINDINGS_20261025.md` and `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md`.
## Completion decisions — 25 October 2026

- Keep the fixed alpha-standardized empirical reference and `w=alpha` selected mixture target; pooled real answers are secondary. The Adult practical-gain threshold stays 0.005 and the representation constraint remains L1<=0.25 with each `w_i>=0.5 alpha_i` for the challenger.
- End the general Adult weighting search at the corrected registered development result: 0/18 constrained practical-gain slices; retain negative and adverse cells. Choose one global **copula** family by validation-only mean query-max and use exact size weights. Bank results do not reopen Adult selection.
- Treat maintained PGM fitted from identical unnoised aggregate query means as nonprivate same-summary development reference. Treat adapted FLAIM as a different-access fixed-membership privacy reference; its four epsilon-4 fits are distinct releases on overlapping Adult people. Neither creates a full-pipeline DP claim or an equal-access superiority result.
- Freeze the official Adult procedure in canonical `SELECTION_FROZEN.json` with SHA-256 `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. The gate accepted before first official-test read at 2026-10-25T05:40:33Z. No test-derived method, threshold or seed change is authorized.
- Default conditional route is support-gated direct teacher rejection; trained per-condition students remain development alternatives. Probability calibration uses independent source-specific sets and Platt sigmoid. Approximate copula joint scores are not called exact projected probabilities.
- Measured model-plus-metadata payloads exceed matched raw-table payloads in all three audited aggregate cells, so no compression claim is retained for copula releases. The main pipeline is nonprivate; the atom-aware histogram and FLAIM references have narrower separate privacy contracts.

# Terminal experimental decision — 25 October 2026 (supersedes provisional notes below)

- Retain one globally selected projected **copula** family and exact size weights `w=alpha`. Its frozen constrained comparator did not reach the registered practical −0.005 gain on official Adult test (overall difference −0.000215; zero of six slices). The fallback is a bounded empirical decision, not a theorem of size-weight optimality.
- Declare the twelve work packages closed at the precise scopes in `EXPERIMENTS_01_TO_12_CLOSURE.md`. Bank external replication also failed the transferred practical margin. Keep null/adverse rows and unsupported wide claims visible.
- Treat official test as accessed once after written freeze at 2026-10-25T05:40:33Z, with seeds404/505 used for confirmation only. Do not reselect from the official-test leaderboard.
- Retain the main pipeline as nonprivate; avoid a compression assertion because matched copula payloads exceeded raw-table bytes. PGM is a same-unnoised-summary nonprivate reference, adapted FLAIM a different-access private reference, and HeteroFedSyn has no numerical ranking here.
- Package the evidence for academic review without publication, public push, neural training or external contact.

# Postdelivery audit decision — 25 October 2026 (current)

- Keep the frozen copula/size procedure, 12 official-test primary and secondary cell outputs, practical margin and all scientific conclusions unchanged. The current 91-test suite and freeze validator passed again.
- Preserve version-1 archive and its SHA as historical delivery. Issue a distinct version-2 archive because the first package's closure cited one nonexistent report path and its reproduction command used the original handoff verifier on edited files.
- Interpret `FIRST_OFFICIAL_TEST_READ.json` as first **confirmation-scoring** access after freeze. `adult.test` was physically read earlier for source validation and exact duplicate quarantine, without scoring or selection; document the distinction rather than rewriting the immutable access record.
- Use the Airbag PAST/PRESENT/FUTURE gate for the clean-extraction check. Do not expand Adult weighting search or use test outcomes to alter the method while repairing package documentation.

# Final postdelivery decision — 25 October 2026 (current)

- Use version-2 private archive SHA-256 `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf` as the authoritative handoff. Version 1 remains preserved as a historical delivery. The laptop receipt and terminal JSON are beside the ZIP; the archived status snapshot predates transfer completion.
- The package repair changed documentation, portable bootstrap and historical audit compatibility only. Frozen copula/size scoring source, official-test choices, data and metrics remain unchanged. The exact final ZIP passed clean-extraction checks.
- State the first official-test timestamp as first **confirmation-scoring** read after the freeze; raw source/quarantine reads occurred earlier. Retain the Adult/Bank practical-gain null result, nonprivate main release, and explicit wider empirical/theory limits.

