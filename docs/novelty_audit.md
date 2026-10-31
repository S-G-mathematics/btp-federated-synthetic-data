# Initial novelty audit -- no originality conclusion yet

All eight candidate families have statistical precedent. This repository supplies clearly labeled adaptations and comparisons, not eight invented algorithms. Their collection is not itself proof of originality.

The proposed research question is whether an explicitly limited release of local non-neural distributions and statistical metadata supports an effective, stable weighting/aggregation procedure for empirical reconstruction of heterogeneous clients, conditional sampling and income prediction. A contribution must identify a concrete mechanism, useful guarantee, or well-controlled new finding after comparing the closest relevant prior work.

Core overlap to challenge: Fed-TGAN similarity/quantity-aware parameter averaging; FedGMM/FedEM mixture weights; multiple-source adaptation/FedGO density-sensitive prediction; stacking and predictive score methods; entropy balancing/KMM; Private-PGM/AIM/FLAIM/HeteroFedSyn noisy-statistical fitting, workload awareness and federated heterogeneity.

Possible findings to investigate, not claims: which released statistics identify useful corrections; when size weights should be retained; uncertainty-aware versus point calibration; representation/support constraints for rare conditions; communication/privacy versus conditional fidelity; whether simple frozen rules transfer to new partition cases.

Before the final paper: inspect primary full texts and released code, record exact assumptions and objective differences, compare within information-access tracks, identify indistinguishable/equivalent candidate rules, separate finite-support approximations, repeat independent algorithm/split seeds and add external datasets when feasible. Preserve null/negative findings. A theoretical proposition requires a mathematical proof, while experiments test its empirical implications and hypotheses.


## Primary-source check ? 2026-10-24

This pass checked the linked primary publisher/arXiv abstracts. It is an initial overlap screen, not a full-text/code replication or an originality verdict.

| Prior work | Verified scope from primary source | Boundary for this BTP |
|---|---|---|
| [Fed-TGAN](https://arxiv.org/abs/2108.07927) | Tabular GAN federation with multi-source feature encoding and table-similarity-aware weighting of local models. | Similarity/quantity weighting is prior art; our non-neural released-distribution mixture is a different object, not an invented weighting concept. |
| [FedGMM](https://proceedings.mlr.press/v202/wu23z.html) | Federated EM estimates GMM input distributions for personalized learning and new-client adaptation. | GMM density fitting and federated mixture structure are prior art; our target is empirical synthetic-data reconstruction under fixed client mass. |
| [Agnostic Federated Learning](https://proceedings.mlr.press/v97/mohri19a.html) | Optimizes predictive performance for any target mixture of client distributions, with fairness and learning guarantees. | Our uncertainty-adjusted query reconstruction objective is distinct and must not be described as faithful AFL. |
| [FLAIM](https://arxiv.org/abs/2310.03447) | Federated AIM-style private tabular synthesis addresses heterogeneity with a private proxy. | Federated workload/marginal selection and heterogeneity correction are prior art; our unnoised summaries are not a DP variant. |
| [HeteroFedSyn](https://arxiv.org/abs/2603.08832) | Private horizontal federated tabular synthesis uses two-way marginals and adaptive distributed dependency selection. | Privacy-aware heterogeneity correction is prior art; our standalone histogram baseline does not make the full pipeline DP. |

Next audit step: read full methods and released code for the closest work, compare exact objectives, access assumptions, and evaluation protocols, then test any proposed contribution against these baselines. No novelty claim is established by this abstract-level check.


## Supervisor-directed primary-source comparison (2026-10-24 UTC)

This pass read the primary paper text or author repository landing/replication instructions, not a code-level reproduction. The comparisons below prevent misplaced novelty and define an access-matched baseline boundary.

| Primary source | Directly verified mechanism | BTP comparison boundary |
|---|---|---|
| Yao et al., Using stacking to average Bayesian predictive distributions, https://arxiv.org/abs/1704.02030 | Stacking combines predictive distributions using proper scoring rules and compares BMA and pseudo-BMA. | F1/F2/F3 are established predictive combination ideas. Our frozen candidate distributions and privileged common-reference scores are a particular application, not a new stacking method. |
| McKenna et al., Graphical-model based estimation and inference for differential privacy, https://proceedings.mlr.press/v97/mckenna19a.html | Fits a graphical model to noisy low-dimensional distribution measurements for downstream query inference. | Query/marginal measurement fitting alone is established; our unnoised aggregate calibration summaries are not a DP Private-PGM analogue. |
| Maddock et al., FLAIM, https://arxiv.org/html/2310.03447v3 ; author code https://github.com/Samuel-Maddock/flaim | Iterative federated AIM uses local marginal selection, secure aggregation of measurements, Gaussian noise, a heterogeneity proxy from 1-way marginals, and PGM updates. The author README supplies replication configs and states Adult requires manual data placement. | Closest operational baseline for a future matched private track, not an equal-access baseline for our current nonprivate model-release mixture. Match dataset version, discretization, query workload, privacy parameters, rounds and communication before numerical comparison; no FLAIM replication has run here. |
| Li et al., HeteroFedSyn preprint, https://arxiv.org/html/2603.08832v1 | Clients share noisy 1-way and projected 2-way marginals; the server measures dependencies, adaptively selects marginals and synthesizes from those measurements. | Heterogeneous federated statistical synthesis, workload selection and released-statistic compression are prior art. Its DP/noisy marginal contract differs from our unnoised released local models and summaries. No objective-matched replication has run here. |

A prospective distinction to test is a **fixed-target representation-constrained rule with a size fallback when finite-sample evidence does not certify a practical gain**. This is a hypothesis and theorem target, not an established novelty claim. The elementary inequality bounding fixed-query change by half the L1 weight shift is standard and will not be claimed as novel. The full-paper/code objective matrix, exact access ledger, FLAIM compatible benchmark and proof or counterexample remain open.

## Empirical novelty reassessment after corrected projected development (2026-10-24 UTC)

The corrected 54-cell development core and selected secondary gates have **not** established a practically superior fixed-target weighting rule. Fixed constrained query-minimax averaged +0.002428 primary error versus tuned size and had 0/18 practical three-seed mean-gain slices. More synthetic rows and more stable finite pilot measurements did not reveal a robust reversal in the selected harder slices. The per-condition trained student often lost to direct teacher rejection, while the repaired independent histogram remained structurally too weak to make a full-pipeline privacy/utility contribution. These are bounded Adult development observations, not proof that such methods cannot work elsewhere.

The defensible thesis contribution may be a carefully controlled **comparative negative result and fallback protocol**: how target representation, generator defects, pilot uncertainty and access contracts explain apparent weighting gains. It is **not** a claim to invent stacking, KMM, graphical measurement fitting, federated heterogeneity correction or a DP generator. A theorem for finite-sample fallback would need a precise adaptive-selection and noisy-summary analysis beyond the elementary L1 query bound; no such theorem has been proved here. FLAIM, HeteroFedSyn and external-dataset objective/access-matched comparisons remain needed before broad originality or transfer claims. The draft decision and complete evidence links are in `docs/GLOBAL_DEVELOPMENT_DECISION_DRAFT_20261024.md` and `docs/EVIDENCE_INDEX.md`.

The 25 October finite-query conditional ratio proposition is another **elementary algebraic bound**, not a new theorem contribution. Its binary counterexample shows that matching one-way queries cannot guarantee an unmeasured conditional or predictor. The six-cell support audit supplies bounded empirical evidence for the registered conditions only; it does not create an arbitrary-condition or novel-transfer claim. Evidence: `docs/FINITE_QUERY_TRANSFER_PROPOSITION_20261025.md` and `docs/PROJECTED_TRANSFER_FINDINGS_20261025.md`.
