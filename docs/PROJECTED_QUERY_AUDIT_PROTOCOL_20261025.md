# Projected query-level fidelity and uncertainty protocol

**Fixed:** 25 October 2026 local time, after the six-cell joint-prediction audit and before query-level results. Development assessment only; official Adult test and confirmation seeds404/505 remain locked.

Use the same six corrected projected model cells (Chow-Liu age/K5 and mixed-GMM label-skew/K10, seeds101/202/303), the exact size and fixed constrained weight vectors, the declared version-2 primary and unseen-audit workloads, and the alpha-standardized real development-assessment reference. Regenerate exactly five 10,000-row D_S draws for each method/cell with the original public assessment seeds `split_seed+5200+rep`; reject a cell if the resulting primary query maximum differs from its saved constrained-audit metric. Keep the unweighted pooled held-out answer separately labeled, never substitute it for the alpha target.

Save each real alpha/pooled and synthetic answer and signed/absolute error for every query, method, seed and draw. Stratify by query arity and real-alpha support: rare `<1%`, low `1–5%`, common `>=5%`. Report max/mean error and which queries dominate the maximum, retaining unseen interactions. Do not fit weights or revise workloads from these answers.

For a hypothetical independent real sample within each client and an independent m-row synthetic sample, provide the simultaneous 95% Hoeffding/union bound on all L declared bounded [0,1] queries:

`r = sqrt(0.5 * log(2L/0.05) * (sum_i alpha_i^2/n_i + 1/m))`.

This bounds the difference between empirical and expected two-sample query differences under those sampling assumptions. Adult records and overlapping split seeds need not be independent random cohorts; therefore the radius is a **conditional reference calculation**, not a validated confidence interval or a measured population error. Five synthetic draws describe Monte Carlo variability separately. No naive empirical-versus-model continuous TV estimate is made. Run under the shared one-worker lease and retain failures.
