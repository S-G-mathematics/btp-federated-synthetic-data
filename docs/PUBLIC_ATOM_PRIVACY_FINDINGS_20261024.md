# Public zero-atom histogram development findings — 24 October 2026 UTC

## Scope, implementation and evidence

The separate, versioned `scripts/public_atom_histogram.py` uses fixed public bins with dedicated zero atoms for capital gain/loss and deterministic public education-code projection after sampling. Private and nonprivate fits have the same family, schema and five public 10,000-row sampling seeds. Private histogram counts use fresh OS-entropy Laplace noise at scale `30/epsilon` for each of 15 column histograms under **replace-one adjacency, fixed public client membership and fixed public client size**. Count clipping, normalization and education projection are postprocessing. A single such histogram release is epsilon-DP under those assumptions; the main projected models, unnoised summaries, per-record privileged scores, data-dependent assignment, raw research ZIP and complete campaign are **not** DP. Three epsilon settings (1, 4, 8) on the same client records would compose to epsilon 13 if all released; overlap across split seeds and changing assignment require additional accounting that this simulation does not establish. Noise seeds were not serialized; synthetic sampling seeds are public postprocessing.

Six fixed development cells ran (Chow-Liu age/K5 and mixed-GMM label-skew/K10, seeds101/202/303), with matched nonprivate and three private settings, five synthetic draws per setting/cell. All 6/6 cells completed, zero failure files, 78 tests passed, zero invalid income labels and zero mapped education-code violations. Raw model releases, individual ledgers, metrics, membership diagnostics and config hashes are at `results/public_atom_privacy_20261024/`; aggregate CSVs at `reports/public_atom_privacy_20261024/` (laptop copies under `reports/public_atom_privacy_local_20261024/`). Tests: `logs/ec2_tests_public_atom_privacy_20261024.log`. This experiment did not use the official Adult test or confirmation seeds404/505.

## Matched utility and structural fidelity

| Fixed family, three overlapping split seeds | Mechanism | Mean primary query max | Mean capital-gain zero-frequency absolute error | Mean capital-loss zero-frequency absolute error |
| --- | --- | ---: | ---: | ---: |
| Chow-Liu age/K5 | Nonprivate matched | 0.332158 | 0.006317 | 0.003040 |
| Chow-Liu age/K5 | epsilon 1 | 0.337651 | 0.024557 | 0.021197 |
| Chow-Liu age/K5 | epsilon 4 | 0.330778 | 0.010430 | 0.005380 |
| Chow-Liu age/K5 | epsilon 8 | 0.332391 | 0.006990 | 0.004775 |
| GMM label-skew/K10 | Nonprivate matched | 0.334530 | 0.006909 | 0.002202 |
| GMM label-skew/K10 | epsilon 1 | 0.336803 | 0.033822 | 0.036618 |
| GMM label-skew/K10 | epsilon 4 | 0.335477 | 0.013809 | 0.009538 |
| GMM label-skew/K10 | epsilon 8 | 0.334850 | 0.010816 | 0.005318 |

The corrected public atoms substantially represent structural zeros, but an independent-column histogram still has large **~0.33 primary query error** even without noise. Its missing dependencies dominate this bounded comparison. Private epsilon 1 added about +0.005493 mean query max for Chow-Liu age and +0.002273 for GMM label skew relative to the matched nonprivate baseline. Epsilon 4 happened to give a slightly lower mean than nonprivate in the Chow-Liu slice; this is finite noise/sampling variation, not a privacy benefit. Each private setting has one fresh noise fit per cell plus five public synthetic draws, so these draws do not measure DP-noise variability. The histogram models are separate baselines, not a private version of Chow-Liu/GMM or the federated weighting methods.

A **postpilot structural bridge** reran the legacy nonprivate public-bin sampler on the same six train partitions, alpha targets, query workload, 10,000-row counts and public sampling seeds. Its mean primary query max was 0.952704 Chow-Liu age and 0.953165 GMM label skew, versus 0.332158/0.334530 for the corrected nonprivate histogram. Legacy capital-gain zero-frequency absolute error was 0.922977/0.924069, versus 0.006317/0.006909 after repair; legacy mapped education-code mismatch was about 0.82, versus 0. The bridge changes **both** zero atoms and education projection, so its aggregate query improvement is not attributable to either change alone. Evidence: `reports/public_atom_legacy_bridge_20261024/` and `logs/public_atom_legacy_bridge_20261024.log`, with laptop copies under `reports/public_atom_legacy_bridge_local_20261024/`.

Likelihood membership AUC means across client-model diagnostics were about 0.50 for both private and nonprivate fits; individual GMM-cell AUCs varied much more. Those attacks use train members versus development-assessment nonmembers and may reflect distribution shift. **AUC near 0.5 is not a DP proof.** Full release composition, fixed membership assumptions, the raw ZIP, and a matched FLAIM/Private-PGM comparison remain unresolved. No campaign-wide method freeze or official-test confirmation follows.
