# Fixed-target projected-model development matrix

**Dated:** 24 October 2026 UTC. **Status:** completed Exp 1/2 and representation screen; global method selection, downstream gates and official Adult confirmation remain incomplete.

## Contract and execution

The primary empirical reference is the alpha-standardized held-out Adult client data, with alpha fixed by TRAIN client sizes. The measured endpoint is the maximum bounded-query difference between that reference and exactly 10,000 synthetic rows. The ordinary pooled held-out reference is secondary. Adult `fnlwgt` remains a feature. The version 2 workload adds the postpilot education-code relation query; it cannot independently confirm the old version 1 campaign. Every comparison uses the same version 2 workload, local tuning rule, projected public education map, split manifests, local model checkpoints and five synthetic assessment draws within its cell. No official-test row was scored.

The deterministic run contains the complete **54-cell core**: copula, Chow-Liu and mixed GMM × age, age+education and label skew × K=5/10 × development split seeds101/202/303. Three independent-histogram K=10/seed101 cells are a separate weak-model negative control. The 57 cells produced 741 method-cell rows (13 per cell), under code hash `25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868`. The audit found zero failed local tune trials, zero nonconverged/invalid selected trials and zero failed weight fits; all 57 fixed-pilot mixture oracle LPs succeeded. Exact-score claims apply to the discrete model families, while copula/GMM scores remain approximate. The latest cross-process determinism suite passed 74 tests. The previous projected five-cell pilot is retained but superseded for matched comparisons because the old Chow-Liu sampler used hash-dependent set iteration.

## Weighting versus size

| Three-seed core screen | Within-cell validation-selected release-only rule | Fixed constrained query-minimax rule |
|---|---:|---:|
| Assessment wins over size, individual cells | 28/54 | See paired table; aggregate below |
| Individual cells with primary improvement ≥0.005 | 7/54 | 3/54 |
| Generator × partition × K slices with mean improvement ≥0.005 | 1/18 | **0/18** |
| Mean paired primary difference, method minus size | −0.000458 | **+0.002428** |
| Selected weights satisfying L1≤0.25 and every w_i≥0.5α_i | 18/54 | 54/54 by solver certificate |

Negative differences favor weighting. The fixed constrained rule improved three individual GMM cells by the practical margin, but no three-seed slice reached a mean gain of 0.005. Its generator mean differences were Chow-Liu +0.001296, copula +0.001976 and GMM +0.004012. The selected-rule generator means were Chow-Liu +0.000057, copula +0.000919 and GMM −0.002349. These split seeds reuse Adult people; three seeds and five synthetic draws are not independent cohorts or a basis for a conventional independent-cohort confidence interval. The per-slice tables retain each three-seed minimum and maximum.

The **one** validation-selected slice with a three-seed mean practical gain was mixed GMM, label skew, K=10: mean Δ=−0.006951, with all three split seeds showing a negative difference. Its mean L1 weight shift from alpha was **1.222**, far above the registered 0.25 representation budget. On those same saved models and version 2 pilots, constrained weighting had mean Δ=−0.001746, below the practical margin. Thus this apparent fidelity gain does not establish an acceptable fixed-target method. It may change who contributes to the synthetic sample, and its subgroup/utility implications remain unmeasured.

The first full projected development matrix therefore does **not** establish a practical aggregate advantage for the registered representation-constrained rule over tuned size weighting. Size weighting remains the defensible fallback. This is a development conclusion under the stated workload and release contract, not a theorem that weighting cannot help, not statistical equivalence, and not a campaign-wide frozen method.

## Structural and release checks

The 57-cell size-weighted structural audit found a mean education/code relation violation rate 0.000879 (maximum 0.0033) after public projection. Known mapped categories are set to their public code by construction; residual violations are unmapped categories such as `education='?'`, not invented codes. All audited numeric samples were finite integers. The mean capital-gain zero-frequency error was −0.007170, with cell minimum −0.013961; capital-loss mean error was −0.001686. The education relation is substantially repaired, but numeric atoms and subgroup fidelity still need attention. The source real TRAIN map matched the declared public map in every audited cell.

The server release remains **nonprivate**: fitted local models plus unnoised aggregate query/covariance/kernel summaries. F1/F2/F3 continue to use privileged real calibration scores and cannot be compared as equal-access deployable rules. The standalone public-bin DP histogram is a separate mechanism and has not been repaired/rebenchmarked in this version 2 campaign. The fixed map and release bytes are recorded in the per-cell release contracts and first-pilot audit; a complete communication/privacy ledger across every release and repeated setting remains open.

## Evidence and next gate

- Source cells and logs: `results/ec2_projected_v2_deterministic_20261024/`; scheduler logs `logs/projected_v2_deterministic_launcher.log`, `logs/projected_v2_copula_k5_launcher.log`, `logs/projected_v2_k10_seed101_launcher.log`, `logs/projected_v2_seeds202303_launcher.log`.
- Method audit: `reports/ec2_projected_v2_deterministic_20261024/overview.json`, `manifest.csv`, `method_cell_means.csv`, `selected_slice_summary.csv`; generated by `scripts/report_projected_matrix.py`.
- Constrained fits: `results/representation_constrained_projected_v2_deterministic_20261024/` and `reports/representation_constrained_projected_v2_deterministic_20261024/overview.json`, `cell_method_means.csv`, `slice_summary.csv`; generated by the shared-lease `scripts/representation_constrained.py` and report script.
- Structural audit: `reports/structural_features_projected_v2_20261024/cell_diagnostics.csv` and `slice_summary.csv`; generated by `scripts/audit_structural_features.py`. The first provenance-path failure is retained in `logs/structural_features_projected_v2.log`; its corrected rerun completed at `logs/structural_features_projected_v2_retry.log`.
- Correctness and supersession: `logs/ec2_tests_deterministic_chow.log`, `docs/PROJECTED_SAMPLING_DETERMINISM_20261024.md`.

The next gate is matched subgroup coverage and downstream utility for tuned size versus at most two viable candidate rules, followed by conditional support, full-release/privacy/resource accounting, pilot uncertainty and an explicit campaign-wide development-validation decision. Do not open the official Adult test or confirmation seeds404/505 until a procedure and all applicable gates are frozen. If the registered rule continues to miss its margin, record **“no improved weighting method established”** and carry size weighting forward. An external dataset is needed before broad cross-dataset claims.
