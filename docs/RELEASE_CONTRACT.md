# Release and access contract

This is a single-process research simulation of federated roles. File placement
and function arguments enforce the intended access boundary in the study;
they are not a secure distributed implementation. See each cell's
`releases/release_contract.json` for its actual recorded messages.

| Item | Source | Statistical server/evaluator access | Privacy status |
|---|---|---|---|
| Public 15-column support, numeric bounds and vocabularies | `btp.privacy.public_schema()` | Shared before fit | Public by declaration; not fitted from held-out rows |
| Proposed public education-to-number relation | Fixed map in `btp.privacy.public_schema()`; verified against development TRAIN | Declared support for a **future** projected campaign; current historical cells used raw generators | Public map and wrapper unit tested; no projected-campaign release or privacy claim yet |
| Client membership and training counts `n_i` | TRAIN-fitted assignment rule | Released; sets fixed target `alpha_i=n_i/sum n_i` | Membership/counts are declared public for the standalone DP baseline |
| Independent, Chow-Liu, copula, mixed GMM, prototype KDE, latent class checkpoints | Each client TRAIN; LOCAL TUNE selects settings | Released model checkpoints under `releases/` | Nonprivate; models may leak membership or attributes |
| Calibration query means and residual covariance | Client calibration partition, predeclared query workload | Aggregate permitted summary in `releases/permitted_summary.npz` | Unnoised, nonprivate; not protected by the separate histogram mechanism |
| Calibration kernel-feature means | Fixed public feature mapping on client calibration rows | Aggregate permitted summary | Unnoised, nonprivate |
| Per-record real calibration log scores for F1/F2/F3 | Privileged evaluator | Used only inside evaluator for score-weight baselines | Privileged comparison; no model-only deployability claim |
| Synthetic pilot rows and finite candidate support | Sampled from released models | Used to fit weights/logpool/barycenter | Post-model outputs; not DP merely by being synthetic |
| Validation/assessment/official-test real rows | Privileged evaluator | Metrics and oracle diagnostics only, except explicitly privileged scores above | Never deployable statistical-server training inputs |
| Published Genuity KDE/copula fitted objects | Each client TRAIN | Remain in client simulation process; only synthetic rows leave | Sample-only comparator; no BTP model-release or DP claim |
| Public-bin Laplace histograms | Each client TRAIN, fixed public sizes/schema | Separate released baseline | Epsilon-DP only under replacement adjacency, fresh private OS noise and ledger scope in `docs/PRIVACY_PROTOCOL.md` |

The official Adult test is inaccessible to development selection by protocol;
`configuration.json.reference_role` identifies every evaluator reference. The
research ZIP contains real Adult rows and nonprivate model outputs and is not
DP. No live secure aggregation, network isolation, or client trust mechanism
has been implemented.
