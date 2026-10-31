# Experiment 6: Downstream Utility

**Question.** Does synthetic training preserve income probability utility?

**Hypothesis/objective.** Real-trained reference outperformed synthetic-trained predictors at this scope

**Type and status.** completed empirical comparison; `COMPLETE_BOUNDED_FINDING` in the dated twelve-package closure. The files linked below record historical execution. This guide is a packaging-time index, not a new experiment.

**Dataset and data roles.** Official UCI Adult is the primary dataset; Experiment 1 additionally includes UCI Bank Marketing `bank-additional-full.csv` as registered external replication. Adult official test was scored only after the campaign freeze. Local fitting uses train/local tune, weighting uses permitted calibration summaries, and a privileged evaluator scores held-out real references. Bank's `duration` is excluded. See [data protocol](../../docs/DATA_PROTOCOL.md), [Bank protocol](../../docs/EXTERNAL_BANK_PROTOCOL.md), [access contract](../../docs/RELEASE_CONTRACT.md) and [freeze](../../SELECTION_FROZEN.json).

**Models and methods.** synthetic-trained and privileged real-trained logistic regression and extra trees. All clients use the same schema. The final Adult generator is train/local-tune-selected projected copula; the main weight comparator uses the fixed alpha target, L1 budget 0.25 and floor 0.5 alpha. Other families or access levels in historical results are labelled separately.

**Partitions, clients and seeds.** The corrected core uses age, age+education and label-skew assignments, K=5/10, seeds 101/202/303. Frozen Adult confirmation uses 404/505; Bank replication uses its registered split and 611/622/633. Experiment-specific subsets, severity seeds, pilot and draw streams are recorded in the linked evidence and [configuration](../../configs/campaign.yaml). Do not infer that all combinations were run in this package.

**Synthetic and pilot budgets.** The primary Adult/Bank comparison uses m=10,000 and five synthetic draws. Exp2 varies pilots 500/1,500/5,000/15,000; Exp4 varies m=2,500/10,000/40,000. Other conditional or private budgets are in their fixed protocols and run manifests.

**Metric and aggregation.** Brier, AUROC, AUPRC, log loss, subgroup coverage. Lower is better for query error and Brier; higher is better for AUROC/AUPRC. Primary paired contrast is challenger minus size; negative favours challenger. Draws are averaged within a cell before slice/overall summaries. The exact unit for this package is in the evidence tables; seeds and draws reuse people and are not independent cohorts.

**Executable source/configuration.** [Package](../../btp/), [experiment runners](../../scripts/), [campaign settings](../../configs/campaign.yaml), [resource limits](../../configs/resources.yaml), [environment lock](../../environment/requirements_final_portable_20261025.txt). `python scripts/reproduce_repository.py --tables` rebuilds saved-result reports without fitting. Full historical execution commands and resource limits are in [REPRODUCE](../../REPRODUCE.md); a specific cell must be explicitly selected there. No default command launches a campaign.

**Expected outputs.** Canonical files below, retained report tables in `reports/`, inspectable author tables in `AUTHOR_READY/PAPER_TABLES/`, and full checkpoints/draws in the verified v2 archive manifest. The latter are not silently duplicated in Git.

**Recorded result.** At registered unequal budgets, size logistic Brier 0.129818 versus privileged TRTR 0.101987 and AUROC 0.856167 versus 0.904646. TRTR used 21,148/4,880/3,254 real train/tune/calibration rows versus 10,000/2,000/2,000 generated rows; no matched-size effect inferred.

**Interpretation.** Real-trained reference outperformed synthetic-trained predictors at this scope

**Limitations/exclusions.** Independent cohort utility and small unsupported subgroups. Forbidden extension: Synthetic-over-real superiority

**Evidence stage.** development and frozen confirmation. Historical source files are retained, and packaging-time checks appear separately in `logs/packaging/` when run. Missing in-Git evidence links: none.

**Canonical evidence and provenance.**
- [docs/FROZEN_CONFIRMATION_FINDINGS.md](../../docs/FROZEN_CONFIRMATION_FINDINGS.md)
- [reports/final_build/confirmation_utility.csv](../../reports/final_build/confirmation_utility.csv)

See [closure register](../../EXPERIMENTS_01_TO_12_CLOSURE.json), [full archive manifest](../../artifacts/full_archive_manifest_v2.json), [claim map](../../results/summaries/claim_to_evidence.csv), and [source mapping](../../provenance/source_to_repository_map.csv).
