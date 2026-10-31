# Theory-only backlog for the author

These are proof and interpretation tasks. **No new fitting, dataset, baseline or confirmation task is hidden here.** The empirical claims in this handoff do not depend on solving them.

1. **Finite-sample fallback rule.** Define a representation-constrained calibration set, a practical margin and a size-weight fallback. Seek a finite-sample certificate that accounts for noisy real summaries, synthetic pilot error, adaptive selection and any declared privacy noise. State assumptions and failure probability; construct counterexamples when the certificate is vacuous.
2. **Representation bound sharpness.** For `H` with bounded empirical client-query entries, characterize when `||H(w-alpha)||_infty <= 0.5||w-alpha||_1` is attained and how observable subgroup constraints supplement client-mass constraints. This elementary inequality is not presented as a new theorem.
3. **Projected pushforward distributions.** Formalize `Q_T(z)=sum_{u:T(u)=z}Q(u)` for finite deterministic schema repairs and specify when exact marginalization is computationally feasible. Distinguish it from rounded/clipped continuous-score approximations.
4. **Support-dependent conditional transfer.** State the finite-query ratio bound under positive condition mass; track teacher mismatch, separately trained student error and low-support denominator amplification. Provide binary counterexamples to arbitrary-condition claims.
5. **Finite-support pooling approximation.** Bound, under explicit assumptions, how empirical geometric or entropic transport support size, smoothing and projection change a finite query workload; distinguish these finite operators from population-optimal continuous pools.
6. **Prospective private framework, separate from this thesis claim.** A future end-to-end guarantee would require fixed or private membership/alpha, protected model/summary/tuning/selection releases, composition across overlapping fits and a declared trust model. It is not a theoretical proof owed for the current nonprivate pipeline.

Formal novelty and publication suitability are for the author and supervisor to assess. A proof should not retroactively upgrade the saved empirical study or change the frozen estimand.
