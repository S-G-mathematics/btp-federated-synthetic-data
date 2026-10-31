# Proposed Adult structural projection contract

**Status:** full 54-cell projected Exp 1/2 development core completed, dated 24 October 2026 UTC. `btp.projection.EducationNumberProjection`, the fixed map in `btp.privacy.public_schema`, the version 2 workload, and a separate `projected_pilot` driver profile are implemented. See `docs/PROJECTED_MATRIX_FINDINGS_20261024.md` for the corrected deterministic three-seed results. The original 54-cell raw-model projection remains an evaluator postpilot ablation. No global frozen method, conditional/predictive projected rerun, full-pipeline privacy claim or official-test evaluation has occurred.

## Public support and release

The Adult education category to education-number mapping in scripts/education_projection_ablation.py was fixed and verified on development TRAIN; no official-test row was used. The same map is now declared in `btp.privacy.public_schema`. To make it a deployable statistical-server operation, record its exact serialized bytes/version in each release ledger and apply the wrapper to every candidate generator and aggregation operator. Keep education='?' explicit. The current postpilot ablation and wrapper leave such rows unprojected; a future policy must either retain that explicitly unsupported stratum and report it or predeclare a rejection/abstention rule and its acceptance cost. Do not silently invent a number for '?'.

The public support change is versioned in a new result root. `btp.projected_workload.projected_workloads_v2` and `docs/PROJECTED_WORKLOAD_V2.md` declare the postpilot structural query extension. All 54 core development cells used that workload, locally retuned the projected sampler, and used projected synthetic pilots, kernel embeddings, calibration H and final D_S. Historical raw checkpoints, scores, pilot matrices, synthetic rows and outcomes remain intact. Conditional teacher/student and predictive stages have **not** been rerun on the projected profile. The fixed alpha target and split manifests remain unchanged.

## Likelihood of projected rows

Let P_i be a fitted raw local joint distribution and T set education-number to m(education) for mapped categories, leaving unmapped education='?' rows unchanged. The emitted distribution is the pushforward T#P_i. For a projected row z with known education e and education-number m(e),

    (T#P_i)(z) = sum_{v in S_EN} P_i(z with education-number replaced by v),

where S_EN is the declared raw integer support for education-number. A known-category row with a different education-number has projected mass zero. For unmapped education, T is the identity and the raw score applies. The sum can be evaluated with log-sum-exp over the finite support, in bounded chunks. This is an exact projected mass only when P_i provides an exact normalized integer joint mass, such as the declared independent/Chow-Liu/latent-class models. Copula and rounded/clipped GMM scores remain approximate after the same calculation. Never compare their score units across families as if exact.

F1/F2/F3 privileged real calibration scores must be recomputed from the projected model if they are reported as predictive scores for emitted rows. An old raw log-score matrix is not that objective. The map itself is public postprocessing, but the fitted client models and unnoised calibration summaries remain nonprivate. The separate DP public-bin histogram could postprocess its samples under a public map without weakening its own stated DP guarantee, but its existing coarse-bin capital-zero defect and full-release accounting remain unresolved.

## Required checks before scaling the projected campaign

1. The map was verified against TRAIN only. Exact normalization of projected discrete models, sampling frequencies and off-map negative-infinity scores passed unit tests. Repeat fit-level support checks in each new generator cell.
2. Confirm integer support, income labels, unknown-education handling and deterministic seeds. Preserve exact largest-remainder mixture counts.
3. The first Chow-Liu cell locally tuned projected candidates with the same pilot grid and saved selected settings. Continue across registered generators, partitions, K and seeds with the same version 2 workload and matched size baseline. The education relation query is postpilot relative to the raw campaign and cannot independently validate earlier cells.
4. Audit all released metadata, score access and bytes. Treat old raw-model comparisons and the first postpilot mapping ablation as exploratory bridge evidence, not confirmation.
5. Re-evaluate conditional/student and predictive stages on projected teacher samples, then apply representation, utility, subgroup, resource and privacy gates before campaign-wide freeze. The official Adult test remains locked.
