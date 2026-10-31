# Target-representation budget ablation (development only)

The fixed population target remains `alpha_i = n_i / sum(n_i)`. A pilot query
matrix `H` and permitted aggregate calibration query vector `b` are already
released in each cell. The postpilot ablation solves a linear program:

```
minimize  t
subject to -t <= H w - b <= t
           sum_i w_i = 1,  w_i >= 0
           sum_i |w_i - alpha_i| <= delta
```

The absolute deviations are represented by nonnegative auxiliary variables;
SciPy HiGHS returns a global LP solution for the fixed empirical `H` and `b`
when its solver status succeeds. This is a **variant** of query minimax/moment
calibration, not a ninth invention. `delta=0` fixes size weighting; `delta=2`
is the unconstrained query-minimax solution. The prespecified development
grid is `[0, .25, .5, .75, 1, 2]`. The script validates those endpoints and a
known two-client intermediate solution before reading any cell.

`scripts/target_budget_ablation.py` receives only `H`, `b`, `alpha` and released
models for fitting/sampling. The privileged evaluator separately reads real
validation/assessment rows to compute empirical D_R/D_S errors. A delta can
be chosen on validation `query_linf` with unseen query MAE as a tie breaker;
assessment remains descriptive and the official test stays locked. The same
saved client models, pilot matrix, target, partition and sampling budgets are
reused for every delta. The L1 constraint does not by itself prove subgroup
fidelity or privacy; those are separate measurements.

## First measured cells

The K=10 seed101 pilot evaluated three fixed checkpoint/pilot cells with
three independent synthetic draws at each delta. Results and a plotted
validation/assessment trade-off are in `reports/target_budget_20261024/`.
Validation chose delta 0 for copula/label-skew, 0.75 for copula/age, and 2
for independent/age+education. These choices were made before reading their
assessment means. In the latter cell, assessment query max error fell from
about 0.135 at delta 0 to 0.047 at delta 2, while effective contributing
clients fell from about 9.5 to 2.1 and six of ten clients received near-zero
weight. This quantifies the intended fidelity/representation tension in one
split seed; it is not an independent replication or a final candidate choice.
