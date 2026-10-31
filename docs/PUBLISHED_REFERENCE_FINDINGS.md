# Published reference findings (25 October 2026)

## Maintained Private-PGM, matched aggregate-summary access

The pinned `mbi` source commit is `9429881f0f21ef413424f6011b9d6ae20728176d`. Four registered Adult development cells used the same 152 unnoised aggregate calibration query means available to the BTP summary calibration rule. No raw real rows entered the PGM fitter. The finite public domain retained numeric integer bins and structural zero atoms. We used 500 fixed iterations and generated five independent 10,000-row draws per fit. The evaluator decoded uniformly within public integer bins, applied the registered education/education-number projection, and scored original-resolution primary queries against the alpha-standardized held-out development reference. This is **nonprivate measurement fitting**, not a DP run or a faithful FLAIM reproduction.

| Partition, K, seed | PGM query-max | Tuned size query-max | PGM minus size |
| --- | ---: | ---: | ---: |
| age+education, 5, 101 | 0.033187 | 0.030925 | +0.002262 |
| age+education, 5, 202 | 0.024914 | 0.026139 | -0.001225 |
| label-skew, 10, 101 | 0.036291 | 0.030044 | +0.006247 |
| label-skew, 10, 202 | 0.024845 | 0.021668 | +0.003177 |

The fitted model matched calibration query means to approximately `5.37e-05`–`1.11e-04` maximum residual, yet its fresh synthetic draws did not consistently beat tuned size weighting on independent development assessment. This contrast illustrates calibration fit, finite sampling, and held-out error as distinct quantities. Four related cells are not an independent cross-dataset trial. No superiority over Private-PGM is claimed.

Evidence: `reports/published_references/pgm_cell_manifest.json`, each `pgm_*/measurement_package.json`, `pgm_complete.json`, `model_mbi2.npz` and five hashed draws, `pgm_assessment_draws.csv`, `pgm_cell_means.csv`, `pgm_per_query.csv`, `pgm_status.csv`, and `logs/pgm_*.log`. The first fitter attempt failed a strict [0,1] check on a target equal to `1.0000000000000002`; a 1e-9 floating-point tolerance repaired only that guard before assessment scoring. The initial evaluator attempt used the isolated PGM fit environment without pandas; it was rerun using the BTP evaluator environment. Both failures are retained in logs.

## FLAIM DP reference, protocol-mismatched

The official FLAIM source is pinned to commit `3e698da752b4af928a040f645f7e08fa306db4cd` in a separate reference checkout. Its README requests Python 3.9 plus pinned dependencies and an AutoDP source install. A separate Python 3.9.24 environment was installed without changing system Python. The pinned `umap==0.1.1` could not be resolved; the compatibility requirements omit that unused legacy distribution while retaining `umap-learn==0.5.3`. The unpinned `jaxlib` resolved to 0.4.30, incompatible with pinned `jax==0.4.16`; the isolated environment uses `jax==0.4.30`. AutoDP source commit `06489ea485653909397937cf5e3c31d06a677ffe` was installed.

The published checkout also lacks utility exports `DEFAULT_DATA_ROOT` and `WANDB_PROJECT_NAME`, omits the `path_manager` import in its data loader, and unconditionally imports neural CTGAN modules that refer to an absent `FederatedDLConfig`. `scripts/patch_flaim_reference.py` records minimal import repairs to the **separate reference checkout**; the BTP implementation remains unchanged. An initial import waited on shared-host disk pages for over three minutes and was interrupted. A bounded import retry succeeded in 9.74 seconds (`logs/flaim_import_probe_retry1_20261025.log`).

The frozen reference adapter uses the same four fixed Adult development **client train partitions**, a public finite domain preserving zero atoms, the registered primary query cliques, epsilon 4, delta 1e-6, four interactive FLAIM rounds, all clients per round, distributed accounting, and OS-private initial NumPy entropy for the fit. It does not set a public deterministic DP-noise seed. Each saved private fit produced five public-seeded 10,000-row postprocessing draws. The authors' accountant reported epsilon `4.000000000000001` for every fit. A sampling-return-type error occurred after the first private model had been saved; the adapter recovered that exact checkpoint and generated draws without a second private fit. The failed log and recovery metadata remain in the first cell. This is an adapted published-code reference with raw client training access and interactive noisy marginal messages, **not** an access-matched BTP competitor or a verified end-to-end DP guarantee for data-derived client assignment.

| Partition, K, seed | FLAIM projected query-max | Nonprivate size query-max | FLAIM minus size |
| --- | ---: | ---: | ---: |
| age+education, 5, 101 | 0.045446 | 0.030925 | +0.014521 |
| age+education, 5, 202 | 0.040432 | 0.026139 | +0.014293 |
| label-skew, 10, 101 | 0.025215 | 0.030044 | -0.004829 |
| label-skew, 10, 202 | 0.049258 | 0.021668 | +0.027590 |

These four private-noise fits are distinct releases on overlapping Adult people. Conditional on each adapted fit actually satisfying its reported `(epsilon, delta)=(4, 1e-6)` guarantee for the same declared adjacency, trust and fixed-membership setting, **basic sequential composition for all four releases is `(epsilon_total, delta_total)=(16, 4e-6)`**. This is approximate DP accounting for the four fitted releases only; it is not pure epsilon-16 DP, and a tighter bound would require a justified accountant. Five draws from each fixed fit are postprocessing and do not add fit expenditure. This does **not** account for unnoised BTP releases, data-derived partition rules or the full research archive. A matching epsilon-4 histogram exists historically but on different registered generator/partition cells, so it is not presented as an equal-privacy head-to-head. The nonprivate size column is a utility reference only. The result is mixed, with one FLAIM cell improving by 0.004829 and three worsening; no method superiority, equivalence or cross-dataset conclusion follows. Composition reference: Dwork and Roth (2014), Theorem 3.16, https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf.

Evidence: `scripts/fit_flaim_reference.py`, `scripts/report_flaim_reference.py`, `reports/published_references/flaim_*/` (configuration, fit metadata, saved model, five hashed draws and completion marker), `flaim_assessment_draws.csv`, `flaim_cell_means.csv`, `flaim_per_query.csv`, `flaim_status.csv` and `logs/flaim_*.log`. The decoded rows use the common public integer-bin map and deterministic education projection for original-resolution query scoring; preprojection relation violations ranged from about 0.02 to 0.08 across cells. The adapter's extra access and source modifications must accompany any thesis comparison.

## HeteroFedSyn objective/access inspection, no numerical comparator

The authors' separate source repository `XiaochenLi-w/Federated-Tabular-Data-Synthesis-Framework` was inspected at commit `5aec4eac2843eab80924f8c803b1198445b38831`. Its README calls the implementation HoriFedSyn and offers `fed_privsyn_adv`; the Adult config uses bundled `datasets/adult` CSV/split files, epsilon 5, delta 1e-10, 100 bins and 50 update iterations. The paper describes private one/two-way marginal sharing, projected dependency measurement and adaptive marginal selection. This is a different privacy, data and interactive release protocol from the official UCI Adult fixed-target BTP mixture. A matched four-cell adaptation would require versioned input/domain/privacy changes beyond the registered reference phase, so no numerical superiority or failure claim is made against HeteroFedSyn. This is a literature/code access comparison, not a replication.
