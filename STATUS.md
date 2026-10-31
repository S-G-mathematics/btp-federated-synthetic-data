# BTP execution status (2026-10-24 UTC)

## Completed
- Existing EC2 verified as `ip-172-31-11-178`; isolated namespace created under
  `/home/ubuntu/research-director/btp-federated-statistics-20261024/`.
- Original ZIP preserved and SHA-256 matched; bundle verifier passed 338 hashes.
  Adult validation reproduced 48,842 records and 25 quarantined overlaps.
- Pinned BTP environment bootstrapped; latest suite passed 74 tests and Adult data validation reran. Evidence:
  `logs/ec2_tests_projected_full_matrix.log`, `logs/ec2_validate_projected_full_matrix.log`.
- Six non-neural generators ran all twelve starter smoke stages. Evidence:
  `results/ec2_smoke_20261024/`, `results/ec2_smoke_added_20261024/`.
- Full-data Exp 1/2 age, K=5, seed 101 completed for the original four and
  added prototype KDE/latent class generators. Evidence: `results/ec2_pilot_gls_fixed_20261024/`,
  `results/ec2_pilot_added_20261024/`, matching reports and cell execution logs.
  These are development runs only; official test was not scored.
- Initial K=10 age/age+education/label-skew Exp 1/2 grid completed 18/18
  cells. It recorded 12 stacking optimizer failures, retained in
  `results/ec2_development_k10_20261024/`. The corrected rerun completed
  18/18 cells with 234/234 method fits and 18/18 oracle LPs successful,
  no likelihood floors. Evidence: `results/ec2_development_k10_stacking_fixed_20261024/`,
  `reports/development_k10_stacking_fixed_20261024/`.
- All twelve K=5 age+education and label-skew Exp 1/2 cells completed.
  Evidence: `results/ec2_development_skew_20261024/`,
  `reports/ec2_development_skew_20261024/`.
- After local-tune sensitivity, independent histograms and mixed GMM reran
  age K=5 seed101 with expanded grids. Evidence: `results/ec2_pilot_extended_grid_20261024/`,
  `reports/ec2_pilot_extended_grid_20261024/`, `logs/ec2_tests_extended_grid.log`.
- Copula Exp 1/2 replication completed 12/12 cells at K=5/10, three skews,
  development seeds202/303: 156/156 method fits and 12/12 oracle LPs
  succeeded. Evidence: `results/ec2_copula_replication_20261024/`,
  `reports/copula_replication_20261024/`.
- K=5 full-data partition/method audits and fidelity-versus-representation
  plots completed. Evidence: `reports/development_skew_20261024/`,
  `reports/partition_skew_20261024/`, `reports/k5_seed101_diagnostics/`.
- Three K=10 target-distance calibration ablations completed using saved
  checkpoints and permitted summaries; evidence: `reports/target_budget_20261024/`.
- One full-data copula/age/K=5 cell ran all twelve starter stages; a corrected
  teacher-only support gate rerun also completed all twelve and abstained on
  the rare condition. Evidence: `results/ec2_fullstage_dev_20261024/`,
  `results/ec2_fullstage_conditional_gate_20261024/`, `docs/WORK_PACKAGE_AUDIT.md`.
- Published Genuity 2.0.2 wheel installed in separate environment and activated
  using a locally signed user-authorized token. Sample-only KDE/copula
  development comparisons ran; evidence: `docs/GENUITY_ASSESSMENT.md`.

- Current-code copula seed101 parity completed: six Exp 1/2 cells, 78 method rows and six oracle LPs. Combined with seeds202/303, 18 cells share code hash ff7cd479d151 and produce reports/copula_three_seed_20261024/. The within-cell validation choice beat size in 6/18 development assessment cells; mean difference +0.001348 query max (positive is worse). Split seeds reuse Adult records.
- Restricted Genuity token scan found zero matches in 4,362 project files scanned (environment directory excluded); token remains in sibling private directory.

- Bounded Chow-Liu/mixed-GMM age replication completed eight Exp 1/2 cells (K=5/10, seeds202/303), 104 method rows and eight successful fixed-pilot oracle LPs, under the same code hash as copula replication. Validation-selected methods beat size on development assessment in 7/8 cells; mean query max difference -0.017346. Evidence: results/ec2_chow_gmm_replication_20261024/ and reports/chow_gmm_replication_20261024/. This covers age only and three synthetic repeats per cell.

- Supervisor-directed analysis protocol fixed the alpha-standardized empirical reference, size baseline, audit-only query role, provisional delta=0.25 and w_i>=0.5 alpha_i representation limits, 0.005 practical query margin, and five final development draws. Evidence: docs/ANALYSIS_PROTOCOL_20261024.md.
- Removed unseen-audit tie-breaking from per-cell selection; 68 tests pass in logs/ec2_tests_supervisor_protocol.log. Historical bridge found one changed winner in 26 reusable core cells; evidence: docs/SELECTION_BRIDGE_20261024.md and reports/core_selection_bridge_20261024/.
- The 16 missing Chow-Liu/GMM age+education and label-skew seed202/303 Exp1/2 cells completed with 208/208 method fits and 16/16 oracle LPs, code hash 984177ee25c0; evidence: results/ec2_core_skew_fixed_selection_20261024/.

- Matched three-generator core completed 54 Exp1/2 cells: 28 corrected-code cells with 364/364 method fits and 28/28 oracle LPs, plus 26 per-method bridged cells; 702 method-cell rows. Evidence: reports/core_matrix_audit_20261024/, reports/core_matrix_diagnostics_20261024/ and docs/CORE_MATRIX_FINDINGS_20261024.md.
- Fixed representation-constrained LP ran all 54 saved cells with five independent draws for size/constrained/unconstrained. Eight of 18 slices met the 0.005 primary gain margin; four also met the development audit guardrail. Evidence: reports/representation_constrained_20261024/.
- TRAIN-verified education-code structural audit and matched projection completed 54 cells. Raw size-sample relation mismatch averaged 25.4% Chow-Liu, 77.6% copula and 61.2% GMM. Projection reduced Chow-Liu size query max by mean 0.06880 and GMM by 0.00983; after projection no constrained slice retained a 0.005 gain. Initial unknown-category failure retained separately. Evidence: docs/STRUCTURAL_REPAIR_ABLATION_20261024.md and reports/education_projection_20261024/.
- A public education-code map and standalone projected-model wrapper are implemented; exact pushforward score normalization/sampling tests passed for independent, Chow-Liu and latent class. The campaign driver has not been switched to projected models. Evidence: `btp/projection.py`, `tests/test_projection.py`, `docs/PROJECTED_MODEL_CONTRACT.md`, `logs/ec2_tests_projection.log`.
- A versioned future workload adds an education-code relation query and one fixed audit conjunction without altering the historical query lists. Evidence: `btp/projected_workload.py`, `docs/PROJECTED_WORKLOAD_V2.md`.
- The first integrated projected-profile Exp 1/2 full-data cell ran and is retained as **historical, superseded** evidence because Chow-Liu sampling depended on process hash order. Evidence: `docs/PROJECTED_PILOT_FINDINGS_20261024.md`, `results/ec2_projected_v2_pilot_20261024/`.
- A hash-seed-dependent Chow-Liu sampling traversal was fixed and covered by a cross-process regression test. The initial projected five-cell outputs remain historical; the corrected version has a new code hash and result root. Evidence: `docs/PROJECTED_SAMPLING_DETERMINISM_20261024.md`.
- The corrected projected version 2 Exp1/2 core completed all 54 generator × partition × K × seed cells plus three independent negative controls: 741 method rows, 57 successful fixed-pilot LPs, zero failed local tune or weight fits, five assessment draws per method. Constrained weights had 0/18 practical mean-gain slices; mean core paired difference was +0.002428 versus size. The per-cell selected release-only rule had one practical mean-gain slice, mixed GMM label-skew K10, but its mean L1 shift was 1.222, outside the 0.25 representation budget. Evidence: `docs/PROJECTED_MATRIX_FINDINGS_20261024.md`, `reports/ec2_projected_v2_deterministic_20261024/`, `reports/representation_constrained_projected_v2_deterministic_20261024/`.
- Projected structural audit completed 57 cells: numeric integer-invalid rate 0; mean residual education relation violation 0.000879 from unmapped categories; mean capital-gain zero error -0.007170. Evidence: `reports/structural_features_projected_v2_20261024/`.
- Seed202 latent-class/independent challenger screen completed 12/12 cells, 156/156 method fits, 12/12 oracle LPs; raw weighting gains remain one-seed and structurally defective. Evidence: results/ec2_challenger_screen_20261024/.
- Projected subgroup and calibrated utility audit completed six registered development cells, with five independent subgroup draws per method and paired logistic/extra-trees predictions. The EC2 suite passed 76 tests. Chow-Liu age/K5 constrained weights worsened mean primary query max by +0.004626 and maximum supported-subgroup error by +0.015095; mixed-GMM label-skew/K10 improved them by -0.001746 and -0.009256, respectively. Neither family reached the registered -0.005 primary practical-gain margin. Evidence: `docs/PROJECTED_SECONDARY_FINDINGS_20261024.md`, `results/projected_secondary_20261024/`, `reports/projected_secondary_20261024/`, and `logs/ec2_tests_projected_secondary_20261024.log`.
- Fixed-checkpoint sample-size audit completed the same six cells at m=2,500/10,000/40,000, five draws each and 10,000-row compatible reuse. At m=40,000 constrained-minus-size mean primary differences were +0.006713 Chow-Liu age/K5 and +0.001492 mixed-GMM label-skew/K10; neither reaches a practical gain. All six cells completed without failure; 76 tests pass. Evidence: `docs/PROJECTED_SAMPLE_SIZE_FINDINGS_20261024.md`, `results/projected_sample_size_20261024/`, `reports/projected_sample_size_20261024/`, `logs/ec2_tests_projected_sample_size_20261024.log`.
- A serialized artifact/access ledger inventoried all 54 projected core cells: 405 client-model files totaling 45,838,513 bytes and 54 unnoised summary files totaling 8,668,152 bytes. These are disk bytes, not measured network traffic or a DP release guarantee. Evidence: `docs/PROJECTED_RELEASE_LEDGER_20261024.md`, `reports/projected_release_ledger_20261024/`.
- Repeated-pilot sensitivity completed the same six development cells at 500/1,500/5,000/15,000 rows per client, five pilot seeds each. All source H matrices reproduced exactly; no corrected-run failures; 76 tests passed. Same-target finite-H_ref LP excess fell below 0.001 on mean at 15,000 for both families, but no pilot size yielded the registered practical three-seed mean fidelity gain. Evidence: `docs/PROJECTED_PILOT_SENSITIVITY_FINDINGS_20261024.md`, `results/projected_pilot_sensitivity_v2_20261024/`, `reports/projected_pilot_sensitivity_v2_20261024/`.
- Registered-condition audit completed the same six cells for size and constrained weights, with an independent teacher-rejection route matched to the trained student's accepted row count. Direct teacher rejection beat the per-condition student on the age and age+education query-max means; rare doctorate/older-age abstained in all 12 method-cells. Thirty-six saved supported student samples had zero postfilter condition or mapped education-code violations; 76 tests passed. Evidence: `docs/PROJECTED_CONDITIONAL_FINDINGS_20261024.md`, `results/projected_conditionals_v2_20261024/`, `reports/projected_conditionals_v2_20261024/`.
- Versioned public zero-atom histogram baseline completed six matched development cells, epsilon 1/4/8 and nonprivate, five draws each; 78 tests passed. The corrected nonprivate primary max was about 0.332/0.335 in the selected families, versus about 0.953 in a postpilot legacy public-bin bridge that changed both zero atoms and education projection. Fresh-noise DP applies only to an individual histogram release under fixed public membership/size, not the main pipeline. Evidence: `docs/PUBLIC_ATOM_PRIVACY_FINDINGS_20261024.md`, `results/public_atom_privacy_20261024/`, `reports/public_atom_privacy_20261024/`, `reports/public_atom_legacy_bridge_20261024/`.
- A dated campaign-wide development **draft** records “no improved fixed-target weighting method established” and tuned size as provisional fallback, with all alternatives, open gates and official-test lock explicit. It is not `SELECTION_FROZEN.json`. Evidence: `docs/GLOBAL_DEVELOPMENT_DECISION_DRAFT_20261024.md` and updated `docs/novelty_audit.md`.
- Bounded Exp7 joint-implied income audit completed six matched development cells, same people as the trained-predictor audit, with exact projected Chow-Liu versus explicitly approximate mixed-GMM score routes. Observed-row coverage was 100% for both weight rules; Chow-Liu joint Brier beat synthetic logistic in the age cells, while approximate GMM joint Brier/AUROC trailed synthetic logistic in label-skew cells. No failed cells; 79 tests passed. Evidence: `docs/PROJECTED_JOINT_PREDICTION_FINDINGS_20261025.md`, `results/projected_joint_prediction_20261025/`, `reports/projected_joint_prediction_20261025/`.

- Registered Exp8 query-level development audit finished six fixed cells: 10,500 saved answers across 175 queries, two weights and five regenerated draws, all primary maxima matched prior metrics, and 79 tests passed. Chow-Liu constrained-minus-size mean primary max was +0.004626; GMM was -0.001746, short of the -0.005 practical gain. The alpha-versus-pooled real target gap reached 0.009984 in a GMM cell. Evidence: `docs/PROJECTED_QUERY_AUDIT_FINDINGS_20261025.md`, `results/projected_query_audit_20261025/`, `reports/projected_query_audit_20261025/`.

- Exp11 finite-query transfer audit completed six fixed cells with 48 condition bounds, 6,816 teacher query answers and 5,112 student/direct empirical triangles; all regenerated teacher counts/masses matched the earlier conditional audit, and 79 tests passed. The rare condition stayed an abstention in all 12 method-cells despite positive empirical mass. Evidence: `docs/PROJECTED_TRANSFER_FINDINGS_20261025.md`, `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md`, `results/projected_transfer_20261025/`, `reports/projected_transfer_20261025/`.

## Running
- No BTP heavy campaign is active at this checkpoint. No global method freeze or official-test run has occurred.

## Failed
- Initial pilot launch's unreadable EC2 UUID guard: resolved using readable
  DMI vendor/product fields; original log retained.
- A rerun of the original immutable-bundle verifier on the edited project tree reports expected source/document hash mismatches; the preserved original ZIP passed all 338 hashes before edits. The later output is retained at `logs/ec2_verify_projection.log`, not presented as a clean current-tree verification.
- The first projected constrained script rejected a manifest lacking its old `status` column before scoring any cell; corrected reader and retry logs retained. The first projected structural audit wrote data but failed at a relative provenance path; corrected rerun completed. Evidence: `logs/projected_v2_constrained_launcher.log`, `logs/structural_features_projected_v2.log` and their retry logs.
- The new secondary evaluator's first isolated test failed on an import path, corrected before experimental execution. Its first report attempt needed optional `tabulate`; the report now formats Markdown without adding a package. Both errors were software-only and retained in session/tool output; six cell results were not recomputed or omitted.
- The first repeated-pilot attempt stopped before scoring due to JSON tuple/list workload comparison. Its failure is retained under `results/projected_pilot_sensitivity_20261024/`; the normalized comparison runs in a new `projected_pilot_sensitivity_v2_20261024` root.
- The first conditional one-cell comparison had unequal teacher/student evaluation row counts. It is retained as historical under `results/projected_conditionals_20261024/`; corrected independent and matched-route results use a new v2 root. A report-only Query type error was fixed without changing cell data; both report logs are retained.
- Original GLS solver failed in three pilot cells: scaled objective and
  analytic gradient fixed it; original failures retained under `logs/initial_pilot_*`.
- Finite-difference stacking SLSQP failed in 12/18 initial K=10 cells and
  one K=5 label-skew cell. Replays on three saved cells showed analytic-gradient
  optimization with dual gap below 1e-6. The solver is repaired and 64 tests
  pass; corrected rerun completed. Evidence: `reports/stacking_solver_audit/`.
- First Genuity activation failed with a malformed token; resolved by a
  locally signed replacement under user authorization. Original failure retained.
- EC2 Luna read-only worker sandbox could not initialize loopback; manual
  airbag review continues. Evidence: `docs/WORKER_ASSIGNMENTS.md`.

## Planned
- Expand training grids where learning curves warrant; retain failed trials.
- Write the campaign-wide development decision memo, complete claim-specific work in the remaining twelve packages, and pursue external/matched prior-work replication where feasible. Actual network traffic and arbitrary-condition generalization remain unmeasured. No official-test run before a complete written global freeze.
- Extend the broad twelve scientific packages, assess viable development
  candidates across utility/privacy/resources, then freeze a global method
  from validation before any official-test confirmation.
- Extend Genuity projected copula sample-only comparison to K=10/seeds if
  useful; keep it outside model-release weighting claims.

Smoke completion and partial split-seed replication are not a scientific ranking, novelty
claim, DP claim, or publication-ready result.
# Completion checkpoint — 25 October 2026 (supersedes earlier planned/locked notes below)

## Completed
- Corrected Adult 54+3 development evidence reproduced; constrained weighting reached 0/18 practical-gain slices, mean constrained-minus-size +0.002428. Projection/score audit and pre-freeze 91-test suite passed.
- Global validation-only generator selection chose projected copula, mean validation query-max 0.029975, with exact `w=alpha` size weighting retained. Official Bank external replication completed 12/12 cells; 0/4 slices reached the transferred -0.005 gain.
- Exp9/10 registered contrasts completed: 12 same-row projection, six release-summary and six fixed-quantity severity cells. Four matched nonprivate Private-PGM and four adapted different-access FLAIM reference cells completed, with retained failed attempts.
- Three copula release payload cells were metered under matching pickle5+gzip6 serialization; model plus metadata was 1.915–2.866 times raw-table bytes. Full release/privacy ledger documents the main nonprivate pipeline.
- Campaign `SELECTION_FROZEN.json` accepted with SHA-256 `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. First official-test read: 2026-10-25T05:40:33Z, after freeze. All 12 primary official confirmation cells finished with no failures.

## Running
- Frozen secondary official confirmation utility and conditional endpoints, sequentially under the shared BTP lease; aggregate reporting/package follows.

## Failed
- Current completion attempts and repairs are retained in logs: first selector counted three controls; first PGM target guard rejected a floating-point ulp; first PGM evaluator lacked pandas in the fit environment; FLAIM required isolated dependency/import repairs and its first post-fit sampler adapter was corrected without rerunning the private fit. No primary confirmation cell failed.

## Planned
- Finish secondary 12-cell pass, aggregate audited tables/plots, twelve-package closure, reproducibility/novelty records and final hash-verified archive copied to the laptop. No method reselection or added official-test hypothesis.

# Terminal completion checkpoint — 25 October 2026 (supersedes historical notes below)

## Completed

- Frozen Adult confirmation: 12/12 primary and 12/12 secondary cells, zero failed cells. First official-test access 2026-10-25T05:40:33Z after accepted freeze SHA `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. Overall size query-max 0.022216; constrained-minus-size −0.000215, zero of six practical-gain slices. Paired utility and support-limited conditional evidence saved.
- External Bank 12/12, registered Exp9/10 24/24, published references four PGM plus four adapted FLAIM, three matched payload audits, twelve-package closure, deterministic report rebuild and clean-room draw recreation completed. The main pipeline is nonprivate.
- Conservative incremental worker upper bound from recorded phase estimates and confirmation elapsed wall interval: 3,351.084 seconds (0.931 hours) versus 24-hour ceiling; no AWS dollar cost inferred. See `reports/resources/completion_runtime.json`.

## Running

- None. The final archive/hash manifest and laptop delivery are verified in the terminal handoff receipt outside the immutable archive. No experimental fit remains active.

## Failed / limits

- No frozen confirmation cell failed. Historical attempts and report-only fixes are preserved in `ALL_FAILURES_AND_REPAIRS.md`. General weighting superiority, whole-pipeline DP, arbitrary-condition fidelity and numerical HeteroFedSyn ranking are not retained claims.

## Planned outside bounded thesis

- Theoretical proof targets in `THEORY_ONLY_BACKLOG.md` and broader empirical ambitions in `EXPERIMENTAL_BLOCKERS.md`; neither changes the frozen result.

# Postdelivery reproduction audit — 25 October 2026 (current; earlier terminal label below superseded)

## Completed

- The version-1 full archive reached the laptop and matched EC2 SHA-256. All registered Adult, Bank, mechanism and published-reference scoring remains terminal. Current EC2 tests: 91 passed; full campaign freeze still accepts copula/size. No frozen scoring input or result changed.
- A full-plan audit found and corrected a wrong Experiment 4 closure link, generic twelve-package stop criteria, an unusable edited-package bootstrap instruction, and ambiguous wording of official-test source reads versus confirmation scoring. See `docs/COMPLETION_REQUIREMENTS_AUDIT_20261025.md` and `docs/POSTDELIVERY_REPAIR_LINEAGE_20261025.md`.

## Running

- Build a separately named version-2 archive, verify every member against its SHA manifest, bootstrap/test a fresh isolated extraction, then copy and checksum the corrected archive on the laptop. No new fitting, method selection or test scoring is authorized by this packaging audit.

## Failed / limits

- Version-1 `REPRODUCE.md` would fail on an edited package; its original ZIP remains preserved as historical delivery. Wider independent-person replication, matched HeteroFedSyn evaluation and whole-pipeline DP are outside retained claims, not hidden completed experiments.

# Verified version-2 delivery — 25 October 2026 (current terminal state)

## Completed

- The corrected full archive was copied to the laptop and matched EC2 SHA-256 `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf` (537,318,039 bytes). All 10,689 ZIP members passed embedded SHA-256 checks on both hosts. Version 1 remains preserved.
- The **exact final ZIP** passed fresh isolated Python 3.12 bootstrap, 91 tests, accepted global freeze, byte-identical saved draw, corrected 57-cell historical audit and deterministic 28-file report rebuild. Final clean-extraction logs are delivered beside the ZIP. All registered Adult, Bank, mechanism and published-reference scoring remains terminal and unchanged.
- `BTP_FINAL_DELIVERY_RECEIPT_20261025_v2.md` and `COMPLETION_STATE_FINAL_20261025.json` beside the laptop ZIP supersede the archived pretransfer status snapshot. The main finding remains no registered practical constrained-weighting gain; the main pipeline is nonprivate.

## Running

- None for the retained bounded experimental thesis.

## Failed / limits

- Version-1 handoff documentation/reproduction defects and the candidate clean-extraction integrity-audit failure are retained with successful repairs in `ALL_FAILURES_AND_REPAIRS.md`. Wider independent-person, matched HeteroFedSyn and whole-pipeline DP studies remain explicitly outside the retained claims.

# Final editorial sign-off and writing handoff — 25 October 2026

## Completed

- Supervisor sign-off accepted `EXPERIMENTAL_WORK_COMPLETE_WITH_EXPLICIT_SCOPE_LIMITS`: eleven bounded findings and one negative/inapplicable subset result. No experimental campaign was reopened.
- `AUTHOR_READY/` now contains the twelve-package acceptance table, claim-to-evidence map, editable 39-table paper set, 15 scientific PNG panels, vector exports for three headline plots, corrected Bank labels, typeset five-page methods/results source and four-page rendered PDF, theory backlog and final sign-off.
- Editorial corrections name the female-condition `relationship=Husband` dependency error (real zero, generated 0.340–0.399, mean 0.375), give actual unequal TRTR/TSTR train/tune/calibration budgets, state FLAIM four-fit conditional composition as `(16,4e-6)`, and remove independent-cohort language. Scientific outputs, original freeze and version-2 archive are unchanged.
- Small addendum ZIP delivered to laptop and existing EC2 project root: SHA256 `cd3d303d40f3c5a9b5f52b5a0e0959dc108cf940c00468aee6801e297ae4d449`. The original version-2 archive still hashes to `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf`.

## Running

- None. No BTP fitting, synthetic generation or scoring process was started for the addendum.

## Failed / limits

- None for the retained bounded thesis. The supervisor review ZIP excludes code/checkpoints; the separate immutable full version-2 archive remains the executable handoff. Publication and theorem novelty require later author/supervisor judgment.

