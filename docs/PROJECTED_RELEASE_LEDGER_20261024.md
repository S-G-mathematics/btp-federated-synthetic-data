# Projected development release and artifact ledger — 24 October 2026 UTC

## Scope and measured bytes

`scripts/report_projected_release_ledger.py` inventoried the **54 corrected projected Exp1/2 core cells** on the existing EC2. It measured serialized file bytes on disk, not network transfer. The implementation simulates clients in one process and does not meter actual messages or implement secure aggregation. Per-cell paths and byte counts are in `reports/projected_release_ledger_20261024/per_cell_artifacts.csv`; category totals are in `category_summary.csv`.

| Category | Files across 54 cells | Serialized bytes total | Mean bytes/cell | Access/interpretation |
| --- | ---: | ---: | ---: | --- |
| Fitted client models | 405 | 45,838,513 | 848,861 | Client-trained model checkpoints supplied to the statistical server; unprotected individual-data influence |
| Unnoised aggregate query/kernel summary | 54 | 8,668,152 | 160,521 | H, target calibration query means/covariance and kernel means; sensitive extra measurements, explicitly nonprivate |
| Client mass/assignment metadata | 54 | 73,710 | 1,365 | Contains data-dependent training counts/alpha and assignment information; protected scope must be declared |
| Public workload/release contract | 108 | 1,779,192 | 32,948 | Declared schema/workload and contract; repeated disk copies are not per-run network traffic |
| Server-derived weight fits | 54 | 600,622 | 11,123 | Includes both release-only and privileged-score candidate records; cannot all be described as same-access server results |
| Server-derived finite operators | 108 | 51,337,824 | 950,700 | Logpool/barycenter output checkpoints, not additional raw client-to-server model messages |
| Privileged row partition manifests | 54 | 38,037,168 | 704,392 | Evaluator-only row assignments; **not** deployable releases |
| Client-private tuning tables | 405 | 1,363,672 | 25,253 | Locally fitted/trial information; **not** deployable releases unless explicitly transmitted |

The categories are serialized artifacts, not an additive privacy budget and not an actual communication bill. A target deployment would need message framing, retransmission, secure aggregation overhead and compression measured separately. Repeated seeds and settings overlap in Adult people; privacy accounting would have to compose any protected releases across them. This ledger currently has no such budget.

## Access boundary

| Step | Statistical server sees | Privileged evaluator sees | Privacy status |
| --- | --- | --- | --- |
| Local training/tuning | Fitted local projected model plus declared metadata | Full local training/tune records in simulation | No DP guarantee for model checkpoints or settings |
| Release-only F4–F8 and size | Models, public schema, client mass, aggregate unnoised calibration query/kernel means and covariance, synthetic pilots | Same plus real rows only for assessment | Unnoised summaries and models are nonprivate |
| F1–F3 score weighting | **Not a model-only deployable protocol in this code** | Per-record real calibration likelihood scores and alpha row weights | Privileged upper-reference track; additional objective/gradient release not implemented |
| Development assessment and TRTR | No held-out real row should enter weight fitting | Development validation/assessment rows; pooled-real TRTR train/tune/cal rows | TRTR is a privileged diagnostic, not a client/server release |
| Official confirmation | Locked, no result generated | Locked, no result generated | Requires campaign-wide freeze before evaluation |

The public education-number mapping is in the declared schema and release contract. `partition_manifest.csv`, source Adult files and the original research ZIP are available in the **research workspace**, which is not a deployable privacy boundary. The standalone public-bin Laplace histogram experiment has a separate, conditional DP claim and does not make the projected model releases, summary methods, score track or ZIP differentially private. Membership-leakage attacks would be diagnostics, not DP proofs. No full-release epsilon, delta, secure aggregation, or measured network-byte claim is made here.

The next privacy/resource work is to repair the public-bin histogram's structural zero representation, compare matched private and nonprivate histograms, and specify protected adjacency, data-dependent sizes/assignment, all repeated releases and randomness. A true distributed communication implementation would be required before reporting actual message bytes.
