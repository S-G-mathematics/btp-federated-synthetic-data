# BTP EC2 handoff: statistical aggregation of non-neural generators

Working title: **A Statistical Framework for Weighted Distribution Aggregation in Heterogeneous Federated Synthetic Data Generation**.

Read `BTP_START_ON_EC2.txt` first. The original ZIP is an execution handoff, not a completed paper. It includes the official UCI Adult archive and original files, cleaned data, source code, tests, configuration, theory, and explicitly labeled local smoke evidence. This extracted EC2 working copy now has measured development runs; see `STATUS.md` and `docs/EVIDENCE_INDEX.md` for their exact scope. The preserved original ZIP itself asserts no EC2 execution.

## What is fixed

- UCI Adult, 48,842 records, 14 predictors plus binary income. All clients have all 15 columns. Five clients first, then ten; non-IID feature, two-feature, and label-skew assignments only.
- A client releases a fitted model and explicitly permitted summaries. Real rows are never statistical-server inputs. Evaluation and privileged calibration-score comparisons have separate access labels.
- The measured fidelity object is **empirical real D_R versus generated D_S**. D_R is not generated. A theoretical unknown population distance is not a measured result.
- Primary metric: target-client-mass-weighted maximum absolute error over predeclared bounded queries. Separate unseen interaction queries, per-column fidelity and downstream utility are co-reported.
- Model choice/tuning uses local tune data. Weight calibration uses a separate calibration split. Oracle weights use validation only. Final test is the official test with duplicate-safe development data.
- Default runs do not score official-test rows: the original validation pool is deterministically divided by full-record hash into oracle/selection validation and development assessment. Tables named `*_test.csv` therefore mean development assessment unless `configuration.json` explicitly says `official_test_confirmation`. To unlock official test, provide `--official-test --selection-file SELECTION_FROZEN.json`; that file must contain the chosen `method` and `test_used_for_selection: false`.
- Eight candidate *families* are evaluated, not eight claimed inventions. Uniform/size weighting and extra calibration variants are baselines. BMA and pseudo-BMA may coincide for fixed models; geometric and transport pooling change the aggregation operator.
- Non-neural generators: mixed independent histograms, Chow-Liu tree, Gaussian copula, transformed mixed Gaussian mixture, compressed prototype KDE, and latent class mixture. A separate published Genuity copula/KDE sample-only comparator keeps its fitted models client-private; see `docs/GENUITY_ASSESSMENT.md`. Approximate likelihoods are labeled. Public ranges/vocab are shared consistently; no global scaler fitted on final test.

## Run on the existing EC2

Use a fresh isolated directory such as `~/research-director/btp-federated-statistics/`. Do not touch Harbor or the separate Experiments 1-6 project. Verify the current machine and configured SSH alias first; old host addresses are not authoritative.

```bash
bash scripts/bootstrap_ec2.sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/run_campaign.py --profile smoke --experiments all
.venv/bin/python scripts/report_results.py --root results --out reports
```

Then run **Experiments 1 and 2 first**, on full Adult at five clients with independently tuned local generators:

```bash
.venv/bin/python scripts/run_campaign.py --profile pilot --experiments 1,2 \
  --generators independent,chow_liu,copula,mixed_gmm \
  --partitions age --clients 5 --seeds 101
```

The scheduler takes one shared heavy-compute lease, checks RAM/disk, limits native threads, enforces subprocess timeouts, checkpoints completed phases and stops on failure. It never provisions, resizes or terminates AWS resources. Respect stricter existing shared-host controls. Default two-hour campaign wall budget is a bounded launch allowance, not an AWS cost estimate. Configure actual dollar limits from the user's existing guard before authorizing new spend.

After integrity, quality, solver, and access-boundary checks, expand development cases and run the remaining stages. `--all-cells` spans all configured generators, partitions, client counts and development seeds; a bounded invocation may finish only a prefix. Re-running resumes matching completed phases. Do not claim the whole grid finished unless its manifest says so.

```bash
.venv/bin/python scripts/run_campaign.py --profile pilot --experiments all --all-cells
```

After a global development decision, a confirmation command is:

```bash
.venv/bin/python scripts/run_campaign.py --profile full --experiments all \
  --generators <frozen-generator> --partitions age,age_education,label_skew \
  --clients 5,10 --seeds 404,505 --official-test --selection-file SELECTION_FROZEN.json
```

For a direct individual cell:

```bash
.venv/bin/python -m btp.run --profile pilot --generator chow_liu \
  --partition age_education --clients 5 --seed 202 --experiments all
```

The direct entry point is for scheduler-controlled/debug use; use `run_campaign.py` for shared-host resource protection.

## Scientific gates

1. Reproduce data audit/tests, then smoke all twelve stages.
2. Run full-data Exp 1/2 development cases; resolve tiny clients, solver failures, poor local models and support loss. Do not silently replace a failed method with size weights.
3. Compare families within their information-access tracks and fixed local generator checkpoints. The mixture LP is exact only for its finite pilot matrix. Nonlinear operators use same-pool best-found references.
4. Freeze a campaign-wide method, hyperparameters and workload using **development validation** results; save a machine-readable decision. The current runner's selection file is only a per-cell validation selection, not this global freeze.
5. Reuse frozen methods in confirmation seeds 404/505. The official test contains the same people across partition seeds, so these are split/algorithm repetitions, not independent new datasets. Bootstrap independent repetition units appropriately; obtain additional datasets for external evidence.
6. Finish the required extensions in `docs/EXPERIMENTS_12.md`, including method-specific ablations and conditional/predictive limitations, before calling a research package scientifically complete.
7. Novelty and publication depend on comparison, sound evidence and actual findings. Negative results are valid. Never force a synthetic-over-real win.

## Artifacts

- `data/raw/`: unmodified UCI archive, original train/test, names files.
- `data/clean/adult_clean.csv.gz`: cleaned full table with stable source row IDs; IDs never become predictors.
- `data/data_manifest.json`, `split_manifest.csv`, `client_partition_manifest.json`: initial audit/splits; each run records its own manifests.
- `btp/`: data, models, weighting, finite-support operators, evaluation, private histogram baseline, driver.
- `configs/`: smoke/pilot/full and shared-resource bounds.
- `tests/`: scientific correctness and leakage invariants.
- `docs/`: protocol, eight-family mapping, twelve-stage contract, model cards, theory, references, limitations.
- `results/smoke_validation/`: actual local mechanical smoke outputs only; `reports/` reproduces their figures.

Only load this package's own trusted pickle checkpoints. They are version-dependent Python objects. Resume requires matching code/config/data fingerprints. Raw results, failed fits and uncertainty must remain available.
