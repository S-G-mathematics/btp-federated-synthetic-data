# BTP experimental closure — executive summary

**25 October 2026. State: experimental work complete with explicit scope limits.** The finished thesis package supports a comparative empirical finding, not a new weighting algorithm or a whole-pipeline privacy claim.

## Question and decision

Under a fixed client-population target `alpha` and an explicit nonprivate release contract, does constrained statistical reweighting improve synthetic-data fidelity over a locally tuned, schema-corrected size-weighted mixture? The primary endpoint is the maximum absolute difference across the registered empirical query workload between a 10,000-row synthetic dataset and an alpha-standardized held-out real reference. A candidate needed a reduction of at least **0.005** at the registered partition/K aggregation unit, while `||w-alpha||_1 <= 0.25` and `w_i >= 0.5 alpha_i`.

**No registered practical improvement was established.** In corrected Adult development, zero of 18 generator/partition/K slices passed the margin; average constrained-minus-size error was **+0.002428**. The global Adult generator was chosen using validation only: projected non-neural copula, with exact size weights `w=alpha`. On official Adult confirmation, its constrained comparator reduced mean query-max by just **0.000215** relative to size weighting, and zero of six partition/K slices reached 0.005. The size procedure's overall official loss was **0.022216**. A separate, prospectively frozen UCI Bank Marketing replication produced zero of four three-seed practical-gain slices, with average difference **−0.001332**. These are bounded null/adverse findings; they do not prove weighting can never help.

## Secondary findings

- On official Adult, real-trained logistic regression had Brier **0.101987** and AUROC **0.904646**, versus synthetic-size logistic **0.129818** and **0.856167** on the same held-out people. Real TRTR used 21,148 train/4,880 tune/3,254 calibration rows; synthetic TSTR used 10,000/2,000/2,000 generated rows. This registered-budget comparison does not establish a matched-size effect.
- The support-gated direct conditional teacher satisfied all accepted conditions, yet the female condition's mean within-condition feature-query maximum was **0.375**. `relationship=Husband` was the worst saved query in all 12 cells: zero in the alpha-standardized real female reference and 0.340–0.399 in generated female rows. The rare older-doctorate request abstained in all 12 cells. This is an observed model dependency failure, not a universal demographic rule.
- Four same-summary, nonprivate Private-PGM fits and four adapted private FLAIM author-code fits gave mixed development results. FLAIM has a different raw-client, interactive, private measurement protocol and is **not** an equal-access ranking against the nonprivate BTP mixture.
- The released copula model plus metadata occupied **1.915–2.866 times** the same-client raw table under matched serialization in three measured cells. The main pipeline is **nonprivate** and has no demonstrated compression or WAN deployment benefit.

## Integrity and access

The campaign freeze is `SELECTION_FROZEN.json`, canonical SHA-256 **`2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`**. It passed the fail-closed gate before the first official Adult **confirmation-scoring** read at **2026-10-25 05:40:33.072893 UTC**. Earlier source-integrity and duplicate-quarantine checks had necessarily read the raw official test without scoring it; see `docs/TEST_ACCESS_SCOPE_CLARIFICATION.md`. Confirmation seeds 404/505 were not used for selection. Twelve primary and twelve secondary confirmation cells completed, each primary cell using five independent 10,000-row draws. The same official people recur across seeds, so draws and split seeds are not independent cohorts. Earlier Adult assessment influenced protocol repair; only the final global generator choice was validation-only.

All twelve registered work packages have a bounded disposition in `EXPERIMENTS_01_TO_12_CLOSURE.md`. Evidence, methods, limitations, and exact reproduction instructions are in `BTP_FINAL_EXPERIMENTAL_REPORT.md`, `REPRODUCE.md`, and `docs/EVIDENCE_INDEX.md`. The separate `THEORY_ONLY_BACKLOG.md` contains proof targets; wider empirical ambitions and their implications are in `EXPERIMENTAL_BLOCKERS.md`.
