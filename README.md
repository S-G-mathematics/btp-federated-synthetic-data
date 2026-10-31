# Weighted Federated Synthetic Data Generation

**Start here:** [Results](docs/RESULTS_AND_STATISTICAL_INFERENCE.md) · [Twelve experiments](experiments/README.md) · [Complete proofs](theory/PROOFS.md) · [Report and manuscript](paper/README.md) · [Reproduce](REPRODUCIBILITY.md) · [Full artifacts](ARTIFACTS.md)

The repository has two reading levels: the guides above provide the research story, while the dated source directories preserve the records behind it. [Repository guide](docs/REPOSITORY_GUIDE.md) explains which files to read and which are historical evidence.

![Adult frozen holdout paired differences](figures/main/adult_frozen_confirmation.png)

The plot shows seed-averaged slice differences, with negative values favouring constrained weighting. The dashed line is the registered practical-gain threshold; no independent-cohort confidence interval is implied.


A reproducible study of representation-constrained aggregation of heterogeneous **non-neural** tabular generators. Each client fits a joint model over the same schema; the statistical server combines released models and permitted summaries to synthesize records. The measured question is whether weighting improves a fixed empirical target over properly tuned size weighting.

## Main answer

The validation-selected Adult procedure uses a projected Gaussian copula, local train/tune model fitting, and size weights `w=alpha`, where `alpha_i=n_i/sum n_j` is the declared client-mass target. The complete procedure was frozen before official-test scoring. The constrained challenger has `||w-alpha||_1<=0.25` and `w_i>=0.5 alpha_i`. The primary paired difference is **challenger minus size**, so negative values favor the challenger:

| Evidence stage | Mean paired difference | Slices reaching the registered -0.005 margin |
| --- | ---: | ---: |
| Corrected Adult development | +0.002427903 | 0 / 18 |
| Frozen Adult official holdout | -0.000214907 | 0 / 6 |
| Registered Bank replication | -0.001331749 | 0 / 4 |

Development slices are generator × partition × client count, averaged across three seeds. Confirmation slices are partition × client count; Bank slices are generator × partition at five clients. These are bounded null/adverse findings, not equivalence or a universal impossibility result. See [all slices](AUTHOR_READY/PAPER_TABLES/), [selection decision](docs/GLOBAL_SELECTION_DECISION.md), [immutable freeze](SELECTION_FROZEN.json), [closure](EXPERIMENTS_01_TO_12_CLOSURE.json) and [sign-off](AUTHOR_READY/FINAL_SIGNOFF.md).

The primary empirical reference is `b_R,l=sum_i alpha_i mean_{z in D_R,i} q_l(z)`; the synthetic answer is `b_S,l=mean_{z in D_S} q_l(z)`. Loss is `max_l |b_S,l-b_R,l|` over 152 registered Adult queries (143 one-way, eight extra two-way, one structural). An additional 23 queries were viewed during development. The official Adult test reused the same people across 12 configurations. `fnlwgt` remains a predictor, not a survey weight.

The frozen conditional teacher satisfied the requested filters, yet the female condition generated `relationship=Husband` at 0.340–0.399 where the alpha-standardized real female conditional reference had zero in the saved cells (mean discrepancy 0.375). The main release is **nonprivate**. Synthetic-trained versus privileged real-trained utility used unequal registered training budgets, which are stated in the tables.

## What this project contributes

The contribution is a reproducible statistical comparison and a boundary analysis: when generator quality, representation constraints, finite pilots, support and evaluation access are controlled, the tested weighting corrections do not establish the registered practical advantage over tuned size weighting. Projection ablations, synthetic-size scaling, conditional support checks, query diagnostics and external replication explain that result. This repository does not claim that standard mixture weighting, query matching, Chow–Liu models, copulas, or privacy composition were invented here.

There are **54 matched core Adult development cells**, plus three separate independent-histogram control cells, producing **741 method rows, 3,705 assessment-draw rows and 57 successful fixed-pilot LP records**. Confirmation and Bank each have 180 saved draw-metric rows. Five synthetic draws within a cell measure generation variability; they are not five independent real datasets.

## Mathematical model and proofs

Client `i` releases a fitted joint generator `Q_i` and explicitly permitted summaries. The server samples from `Q_w = sum_i w_i Q_i`. The measured objective compares the generated table with an alpha-standardized finite real reference:

$$
b_{R,\ell}=\sum_i\alpha_i\,\frac{1}{|D_{R,i}|}\sum_{z\in D_{R,i}}q_\ell(z),\qquad
b_{S,\ell}=\frac{1}{|D_S|}\sum_{z\in D_S}q_\ell(z),\qquad
\mathcal L_{\mathcal Q}(D_S,D_R;\alpha)=\|b_S-b_R\|_\infty.
$$

The [proof supplement](theory/PROOFS.md) ([PDF](theory/proofs.pdf), [LaTeX](theory/proofs.tex)) contains **27 labeled statements: 24 proofs and three counterexamples**, with a [review of assumptions](theory/PROOF_REVIEW.md). It covers representation and sampling bounds, oracle and stability inequalities, subset collapse, conditional generation and support, utility transfer, finite-support approximations, privacy composition, and size-weight optimality boundaries. Standard arguments are identified as such.

- **Exact local models:** size weights recover the declared population mixture and minimize KL and finite-query discrepancy. Uniqueness needs an identifiability assumption.
- **Imperfect models:** size weighting need not be optimal; an explicit feasible two-client counterexample demonstrates this. The supplement gives an approximation bound and a sufficient dual certificate.
- **Likelihood:** client-label multinomial MLE gives observed size proportions. Finite observed-data mixture MLE need not give those weights.
- **Finite-table evaluation:** model-expectation results need sampling and allocation terms before they apply to generated tables. A finite workload does not certify population total variation.

These proofs were consolidated **after** the experiments. The uncertainty-aware fallback and dual certificate are theoretical additions, not retroactively validated parts of the frozen method. [Statement history](theory/post_experiment_additions.md) and the [proof-to-experiment map](theory/proof_to_experiment_map.csv) preserve that distinction.

## Project map

- [`btp/`](btp/): original data, models, weighting, projection, sampling, evaluation and privacy code.
- [`scripts/`](scripts/): original cell runners and report/audit tools; repository-specific lightweight wrappers.
- [`configs/`](configs/), [`environment/`](environment/): frozen campaign/resources and pinned Python dependencies.
- [`data/`](data/): official source variants, cleaning/split manifests and checksum provenance.
- [`results/`](results/), [`reports/`](reports/), [`AUTHOR_READY/`](AUTHOR_READY/): inspectable saved evidence, generated tables, captions and writing material.
- [`theory/`](theory/): complete proof supplement, assumptions, notation and mapping to the original framework.
- [`paper/`](paper/): current report draft, earlier IEEE manuscript, editable source archives and writing status.
- [`artifacts/`](artifacts/), [`provenance/`](provenance/): full-archive manifest, source mapping and exclusion status.
- [`experiments/`](experiments/): twelve evidence-linked work-package guides.

## Experiment index

1. [Experiment 1: fixed target weighting](experiments/exp01_fixed_target_weighting/README.md)
2. [Experiment 2: pilot optimality](experiments/exp02_pilot_optimality/README.md)
3. [Experiment 3: subset composition](experiments/exp03_subset_composition/README.md)
4. [Experiment 4: synthetic sample size](experiments/exp04_synthetic_sample_size/README.md)
5. [Experiment 5: conditional generation](experiments/exp05_conditional_generation/README.md)
6. [Experiment 6: downstream utility](experiments/exp06_downstream_utility/README.md)
7. [Experiment 7: joint implied prediction](experiments/exp07_joint_implied_prediction/README.md)
8. [Experiment 8: query diagnostics](experiments/exp08_query_diagnostics/README.md)
9. [Experiment 9: controlled ablations](experiments/exp09_controlled_ablations/README.md)
10. [Experiment 10: heterogeneity](experiments/exp10_heterogeneity/README.md)
11. [Experiment 11: conditional transfer](experiments/exp11_conditional_transfer/README.md)
12. [Experiment 12: privacy and resources](experiments/exp12_privacy_and_resources/README.md)

## Quick start on Linux/Python 3.12

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r environment/requirements_final_portable_20261025.txt
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/verify_data_sources.py
.venv/bin/python scripts/audit_repository.py
.venv/bin/python scripts/check_theory_examples.py
.venv/bin/python scripts/check_documentation_release.py
.venv/bin/python scripts/reproduce_repository.py --tables
.venv/bin/python scripts/reproduce_repository.py --figures
```

`python -m pytest -q` runs the original scientific test suite. The wrapper only reads saved result files. Full fitting is explicit and governed by [REPRODUCE](REPRODUCE.md) and the shared EC2 resource controller; do not run a campaign just to regenerate figures. The original final-package bootstrap expects the full v2 archive and is not the small Git checkout bootstrap.

To build the standalone proofs, run `pdflatex -halt-on-error proofs.tex` twice from `theory/`. Numerical example checks verify arithmetic, not theorems. The report and IEEE source ZIPs include their own build instructions.

## Evidence, data and limits

[Source and artifact status](ARTIFACTS.md) distinguishes files in Git from the verified 537 MB full archive. Model pickles require trusted provenance and are excluded from normal Git history. [Dataset provenance](data/README_GITHUB.md) records official UCI Adult and Bank sources/CC BY 4.0 attribution. [Theory](theory/README.md), [paper material](paper/README.md), [experimental history](docs/experimental_history.md), [release/privacy ledger](docs/FINAL_RELEASE_AND_PRIVACY_LEDGER.md), [reproducibility levels](REPRODUCIBILITY.md) and [rights](RIGHTS_AND_LICENSING.md) state what the project proves and does not establish. No whole-pipeline DP, arbitrary-condition fidelity, population-TV measurement, independently recruited cohort, or novel weighting-algorithm superiority is claimed. The 12 packages close at their registered bounded scope.

Please cite the research software using [CITATION.cff](CITATION.cff) and cite the original UCI datasets as recorded in their manifests.

**Full checkpoints and saved draws:** [private release archive](https://github.com/S-G-mathematics/btp-federated-synthetic-data/releases/download/repro-2026-10-31/BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip); authenticate with repository access, then verify SHA-256 `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf`.

