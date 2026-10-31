# Release, privacy and communication ledger — 25 October 2026

The main BTP process is a single-host simulation of client, statistical server and privileged evaluator roles. Its fitted local generators, unnoised calibration summaries and synthetic outputs are **nonprivate**. File placement and function arguments document statistical access; they do not implement secure transport or secure aggregation. This ledger supersedes any broad privacy or compression language in earlier development notes.

## Actual released objects and access

| Object | Real-data source / holder | Recipient and purpose | Privacy/access qualification |
| --- | --- | --- | --- |
| Public support, numeric bounds, category vocabulary, education map, query/kernel maps | Predeclared public schema | Every client/server/evaluator | Public by declaration, not fitted on test. Public status is an assumption to validate in deployment. |
| Assignment rule, client IDs, training counts, alpha | Adult training partition; label-skew rule may use Y in assignment | Server target and evaluator routing | Data-derived metadata, unnoised. The standalone histogram DP claim conditions on fixed public membership and sizes. |
| Local independent/Chow-Liu/copula/GMM and other development checkpoints plus tuning selections | Client train/local tune | Statistical server for generation and scoring | Unnoised model releases; not DP. Pickles require trusted loading. |
| Aggregate calibration query means, covariance and kernel feature means | Real client calibration records | Released-summary methods | Extra unnoised, nonprivate measurements; access differs from model-only baselines. |
| Per-record calibration log-score matrix; F1/F2/F3 objectives | Real calibration records | Privileged evaluator only | Privileged access; no secure aggregation protocol or deployable equal-access claim. Approximate score routes stay labelled. |
| Synthetic pilots, finite operator supports, learned weights, generated records, conditional students and income predictors | Released generators and allowed summaries | Server and/or evaluator | Postprocessing of nonprivate inputs, not DP. Support/weight decisions can reveal aggregate information. |
| Validation, development assessment and official-test real records | Privileged evaluator | Metrics, registered oracle diagnostics and TRTR reference | No deployable server fitting access. Official test remains locked until a valid campaign freeze. |
| Public-bin Laplace histogram outputs | Client train, fixed public bins/membership/sizes | Separate baseline | Per fit, epsilon-DP under replace-one adjacency and the assumptions below only. |
| Research ZIP, split manifests, per-record predictions and this deliverable | Local research archive | Authorized researcher/supervisor | Contains public Adult records and nonprivate derivatives; not DP. Credentials and Genuity keys are excluded. |

## Comparable application payload measurement

`scripts/audit_release_payloads.py` reconstructed the same three saved copula development cells (age+education K5; age+education K10; label-skew K10; seed101). Each client model, metadata object and comparison raw training table used **pickle protocol 5 plus gzip level 6**, with counted bytes sent through one local Unix socket pair. Raw training tables remained in the evaluator's comparison path and were not passed to the model-only fitting interface. Application bytes exclude packet framing, TLS, authentication, retries and WAN effects.

| Cell | All raw client tables, bytes | All released models plus metadata, bytes | Ratio | Additional aggregate summary, bytes |
| --- | ---: | ---: | ---: | ---: |
| age+education K5 | 265,949 | 762,098 | 2.866 | 145,317 |
| age+education K10 | 287,339 | 570,000 | 1.984 | 157,267 |
| label-skew K10 | 282,648 | 541,373 | 1.915 | 160,769 |

Thus these copula releases are **larger**, not compressed relative to the identically serialized raw tables. The 25 per-client ratios range 0.969–3.212 (unweighted mean 2.043). The separate aggregate summary is additional traffic; its provenance may involve more than one client message in a real protocol, whereas the counted simulation treats its saved file as one aggregate application payload. Serialized wall times and loopback transfer times are in `reports/resources/application_messages.csv` and `message_totals.csv`; loopback transfer is not a network deployment measurement. No encryption/security claim follows from it.

## Separate histogram mechanism scope

The atom-aware public histogram baseline uses fixed public bins, including capital-gain/loss zero atoms, with fresh OS-entropy Laplace noise of scale `30/epsilon` on 15 column counts. Under replacement adjacency, fixed public client membership and fixed public client size, the declared vector sensitivity is 30 (two affected count entries per 15 columns), so one fit is epsilon-DP under those assumptions. Fixed projection, clipping, normalization and any number of synthetic draws from **one** fit are postprocessing. A public deterministic sampling seed is permissible; exposing/reusing the private noise seed is not.

Releasing epsilon 1, 4 and 8 fits on overlapping records yields the conservative sequential budget epsilon 13 **for those histogram releases alone**. Additional settings, training seeds and any overlapping records need composition. Disjoint-client parallel composition is available only when adjacency and membership actually justify it. Unnoised model/summaries, data-derived partitions, alpha, tuning, support decisions and raw research archive lie outside this isolated proof. No full BTP pipeline DP guarantee has been established. The matched nonprivate histogram still had approximately 0.33 primary query-max error, showing family misspecification dominates this small utility study. Membership attack AUCs around 0.5 are diagnostics, not a DP certificate.

The adapted published FLAIM reference ran four `(epsilon, delta)=(4, 1e-6)` fits. Its authors' accountant reported epsilon 4 per fit. Because the four cells reuse Adult people, releasing all four fits calls for basic sequential composition: **`(epsilon_total, delta_total)=(16, 4e-6)`**, conditional on valid per-fit guarantees under the same stated adjacency, trust and fixed-membership assumptions. This is approximate-DP accounting for those four fits, not pure epsilon-16 DP or a guarantee for the BTP release. The adapter supplies real client training rows and interactive marginal rounds, unlike the BTP aggregate-summary contract. The separate public-bin Laplace histogram releases at epsilon 1, 4 and 8 compose to pure epsilon 13 under their own fixed-membership/replacement-adjacency assumptions only. Neither composition covers unnoised BTP models/summaries, data-derived partition metadata or the research archive. See `docs/PUBLISHED_REFERENCE_FINDINGS.md` and Dwork and Roth (2014), Theorem 3.16: https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf.

Evidence: `reports/resources/release_manifest.json`, `matched_raw_vs_model_payloads.csv`, `application_messages.csv`, `message_totals.csv`, `logs/release_payload_audit_20261025.log`, `docs/PUBLIC_ATOM_PRIVACY_FINDINGS_20261024.md`, and `results/public_atom_privacy_20261024/`. The privacy baseline is not a private version of the copula or constrained weighting rule.
