# Matched Adult development core and fixed-target calibration finding

**Date:** 24 October 2026 UTC. **Role:** exploratory development evidence under docs/ANALYSIS_PROTOCOL_20261024.md. The official Adult test and confirmation seeds404/505 were not scored. No global method is selected here.

## Execution and comparability

The core matrix contains copula, Chow-Liu and mixed GMM × age, age+education and label skew × K=5/10 × split seeds101/202/303 = **54 full-data Exp 1/2 cells**. The 16 previously missing skew/seed202/303 cells and 12 incompatible seed101 Chow-Liu/GMM cells ran under corrected code hash 984177ee25c0. Their 28 cells had **364/364 successful method fits** and **28/28 successful fixed-pilot oracle LPs**, with three assessment synthetic draws per method. The other 26 cells have old code hash ff7cd479d151 and a documented audit-only selection bridge for per-method Exp 1/2 results. Across all 54 cells the paired diagnostic script found 702 per-method rows. The bridge does not validate old selected downstream stages.

The previous within-cell validation-selected rule beat size in 37/54 cells, but its weights satisfied the subsequently declared L1<=0.25 and w_i>=0.5 alpha_i conditions in only 12/54 cells. This is precisely why that per-cell win count cannot establish improvement for a fixed-target application. The principal per-method diagnostic table, including primary/audit query errors, fixed-pilot LP headroom and weight shifts, is reports/core_matrix_diagnostics_20261024/cell_method_diagnostics.csv. Split seeds overlap in Adult source people and are not independent cohorts.

## Predeclared constrained comparison

A separate postcheckpoint LP used only released pilot query means H, aggregate calibration means b and fixed train-mass alpha to minimize ||Hw-b||_infinity under L1(w,alpha)<=0.25 and w_i>=0.5 alpha_i. Size weighting and unconstrained query minimax were matched comparators. Each cell generated exactly 10,000 rows per method with **five independent synthetic draws**. The evaluator then compared D_S with the alpha-standardized real development-assessment reference. It also saved the ordinary pooled held-out reference as a differently labeled secondary estimand. These outputs live under results/representation_constrained_20261024/, with an LP certificate, model/checkpoint reference, split hash, script hash, metrics and completion status in each cell.

All 54 constrained LPs succeeded. Every constrained solution used the full 0.25 L1 budget; the 0.5 alpha floor was binding in 43/54 cells. The alpha-standardized versus ordinary pooled reference query-answer gap ranged from about 0.00089 to 0.00998 across cells (mean about 0.00323), so target definition matters at the declared 0.005 practical margin. Five-draw constrained weighting had lower primary query maximum than size in 37/54 individual cells, but a **practical mean gain of at least 0.005** in only 8/18 generator/partition/K slices. Just 4/18 slices also met the predeclared development unseen-audit deterioration limit of +0.005. These are screens only; downstream utility, observable subgroup coverage, complete release/privacy and resource gates are not yet passed.

| Generator | Partition | K | Mean paired primary Delta | Mean audit Delta | Practical gain and audit screen |
|---|---|---:|---:|---:|---|
| Chow-Liu | age | 5 | -0.02248 | +0.00232 | Pass |
| Chow-Liu | age | 10 | -0.00537 | +0.00705 | Audit fails |
| Chow-Liu | age+education | 5 | -0.01555 | +0.01323 | Audit fails |
| Chow-Liu | age+education | 10 | -0.02583 | +0.00853 | Audit fails |
| Chow-Liu | label skew | 5 | -0.00965 | +0.01071 | Audit fails |
| Chow-Liu | label skew | 10 | -0.02247 | +0.00360 | Pass |
| Copula | age | 5 | +0.00813 | +0.00300 | Primary fails |
| Copula | age | 10 | +0.00305 | +0.00149 | Primary fails |
| Copula | age+education | 5 | +0.00328 | +0.00139 | Primary fails |
| Copula | age+education | 10 | +0.00020 | -0.00030 | Primary fails |
| Copula | label skew | 5 | +0.00054 | -0.00160 | Primary fails |
| Copula | label skew | 10 | +0.00073 | -0.00066 | Primary fails |
| Mixed GMM | age | 5 | -0.00274 | +0.00215 | Practical gain fails |
| Mixed GMM | age | 10 | -0.00808 | -0.00713 | Pass |
| Mixed GMM | age+education | 5 | -0.00142 | -0.00474 | Practical gain fails |
| Mixed GMM | age+education | 10 | -0.00515 | +0.00084 | Pass, margin is close |
| Mixed GMM | label skew | 5 | +0.00041 | +0.00231 | Primary fails |
| Mixed GMM | label skew | 10 | +0.00394 | -0.00006 | Primary fails |

Delta is method minus size error, so negative values favor calibration. Each row averages three overlapping Adult split seeds; each cell mean averages five synthetic draws. Minimum/maximum per-seed Delta, target-estimand gaps, client-mass ratios and synthetic-draw variation are in reports/representation_constrained_20261024/slice_method_summary.csv and cell_method_means.csv. The plot fidelity_representation_frontier.png is generated from those CSVs. No independent-cohort confidence interval is claimed.

## Interpretation and next gates

These results support a **model-family and workload interaction**: the fixed constrained calibration does not produce a practical primary gain for any copula slice; it can substantially improve Chow-Liu primary queries, but four of those six slices miss the registered unseen-audit limit. Mixed GMM has two screen-passing slices, one very near the practical margin. This does not identify a global winner. The 0.25 budget is fully used in every cell, so stronger restrictions or a size fallback may be warranted, but changing them after these outcomes must be labeled an amendment and evaluated afresh.

The next required check is matched local-model quality and structural-zero/dependency repair versus reweighting, plus observable subgroup and downstream-utility comparisons for size and at most two viable constrained candidates. A finite-reference/pilot uncertainty analysis and release/resource ledger are also needed. The registered development audit has now been used as a screen, so it is no longer independent confirmation. A global method freeze and official Adult test remain blocked.

Primary implementation and evidence: scripts/audit_core_matrix.py, scripts/bridge_selection_audit.py, scripts/report_core_matrix.py, scripts/representation_constrained.py, scripts/report_representation_constrained.py, reports/core_matrix_audit_20261024/, reports/core_selection_bridge_20261024/, reports/core_matrix_diagnostics_20261024/ and reports/representation_constrained_20261024/.

## Later same-day structural repair amendment

The TRAIN-verified education-to-education-number mapping ablation in docs/STRUCTURAL_REPAIR_ABLATION_20261024.md changed the interpretation of the four screen-passing raw-generator slices. Mapping the same generated rows reduced Chow-Liu size-weighted query maximum by mean 0.06880 and mixed-GMM size-weighted maximum by 0.00983. After mapping, **no** generator/partition/K slice retained a mean constrained-weighting gain of at least 0.005 over mapped size weighting. The earlier four raw-route screens remain historically accurate but are no longer evidence of a useful improvement over the repaired size baseline. The mapping was introduced after inspecting development outcomes; a prospective structural policy and new validation gates are required before any freeze.
