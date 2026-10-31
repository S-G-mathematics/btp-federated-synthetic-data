"""Create the canonical campaign-wide Adult selection freeze after all gates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, NUMERIC, PREDICTORS
from btp.evaluation import CONDITIONS
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash, param_grid
from scripts.freeze_gate import canonical_bytes, validate_freeze, sha256

FREEZE = ROOT / 'SELECTION_FROZEN.json'
SELECTION_CSV = ROOT / 'reports/completion_selection_20261025/global_generator_validation_selection.csv'
SELECTION_DECISION = ROOT / 'reports/completion_selection_20261025/decision.json'
WORKLOAD = ROOT / 'docs/CONFIRMATION_WORKLOAD_FROZEN.json'
DEPENDENCIES = ROOT / 'environment/requirements_confirmation_20261025.txt'


def relative_hash(path: Path) -> dict:
    return {'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha256(path)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', required=True)
    args = ap.parse_args()
    if FREEZE.exists():
        raise ValueError('Campaign freeze already exists; never overwrite it')
    decision = json.loads(SELECTION_DECISION.read_text())
    if decision['selected_generator'] != 'copula':
        raise ValueError('Saved validation decision differs from registered copula selection')
    if not DEPENDENCIES.exists():
        raise ValueError('Actual pinned-environment freeze is missing')
    if (ROOT / 'reports/confirmation/FIRST_OFFICIAL_TEST_READ.json').exists():
        raise ValueError('Official test access audit already exists before global freeze')
    schema = public_schema()
    primary, audit = projected_workloads_v2(schema)
    workload_record = {'version': 'Q_primary_v2', 'primary': primary.to_dict(),
                       'viewed_development_audit': audit.to_dict(),
                       'status': 'fixed_before_official_confirmation',
                       'source': 'btp.projected_workload.projected_workloads_v2'}
    data = canonical_bytes(workload_record)
    if WORKLOAD.exists() and WORKLOAD.read_bytes() != data:
        raise ValueError('Frozen workload file differs from current implementation')
    WORKLOAD.parent.mkdir(parents=True, exist_ok=True)
    WORKLOAD.write_bytes(data)
    inputs = {name: relative_hash(ROOT / relative) for name, relative in {
        'adult_official_archive': 'data/raw/adult.zip',
        'adult_cleaning_manifest': 'data/data_manifest.json',
        'adult_clean_records': 'data/clean/adult_clean.csv.gz',
        'adult_split_manifest_opening': 'data/split_manifest.csv',
        'global_validation_table': 'reports/completion_selection_20261025/global_generator_validation_selection.csv',
        'global_validation_decision': 'reports/completion_selection_20261025/decision.json',
        'frozen_workload': 'docs/CONFIRMATION_WORKLOAD_FROZEN.json',
        'resources_config': 'configs/resources.yaml',
        'confirmed_python_dependencies': 'environment/requirements_confirmation_20261025.txt',
        'confirmation_runner': 'scripts/run_adult_confirmation.py',
        'secondary_runner': 'scripts/report_adult_confirmation_secondary.py',
        'conditional_service': 'scripts/conditional_service.py',
        'freeze_gate': 'scripts/freeze_gate.py',
        'constrained_solver': 'scripts/representation_constrained.py',
    }.items()}
    now = datetime.now(timezone.utc)
    india = now.astimezone(timezone(timedelta(hours=5, minutes=30)))
    grid = param_grid('copula', {'smoke': False})
    with SELECTION_CSV.open(newline='') as handle:
        family_means = {row['generator']: float(row['mean_validation_query_linf'])
                        for row in csv.DictReader(handle)}
    freeze = {
        'project': 'IIT Guwahati BTP: weighted distribution aggregation in heterogeneous federated synthetic data',
        'protocol_version': 'adult_confirmation_projected_v2_20261025',
        'created_at_utc': now.isoformat(),
        'created_at_asia_kolkata': india.isoformat(),
        'purpose': 'One fixed-target official Adult confirmation of the validation-selected size-weighted non-neural generator and registered comparators',
        'retained_claim': 'Adult development did not establish a practical fidelity gain from constrained weighting over tuned projected size weighting; confirmation checks the frozen fallback and comparator without reselection',
        'selected_generator': 'copula',
        'candidate_families': ['copula', 'chow_liu', 'mixed_gmm'],
        'selection_rule': {
            'data_role': 'development validation only for final generator choice',
            'scope': '18 matched partition/K/seed cells per family; five m=10000 draws averaged within cell; equal cell mean',
            'criterion': 'minimum mean alpha-standardized Q_primary_v2 query-max for projected size weighting',
            'tie_absolute': .001,
            'tie_breaks': ['lower median serialized client model bytes', 'lower median fit seconds', 'lexical family name'],
            'validation_table_sha256': sha256(SELECTION_CSV),
            'decision_sha256': sha256(SELECTION_DECISION),
            'means': family_means,
            'no_assessment_or_official_test_used_for_global_generator_choice': True,
        },
        'local_tuning': {
            'family': 'copula', 'exact_grid': grid,
            'criterion': 'mean absolute Q_primary_v2 difference between local-tune real data and 1000 rows sampled from the candidate local model',
            'fit_data': 'own client train only', 'selection_data': 'own client local tune only',
            'sample_seed': 'master seed + 31*client + 100 + grid_index',
            'finite_score_requirement': 'all of first 64 local-tune scores finite',
            'convergence_and_support': 'candidate requires eligible status and valid income labels; failed candidates retained; no eligible candidate fails cell',
            'ties': 'earliest exact grid entry',
            'score_label': 'approximate mixed-data copula score; not compared across model families',
            'no_new_grid_on_validation_or_test': True,
        },
        'preprocessing': {
            'schema_columns': list(ALL_COLUMNS), 'predictor_columns': list(PREDICTORS),
            'numeric_columns': list(NUMERIC),
            'public_schema': schema,
            'cleaning': 'official UCI Adult train/test whitespace and test label terminal period normalized; ? retained explicit; row_id metadata excluded from predictors',
            'duplicate_contract': '25 official-training rows exactly matching official test quarantined; remaining development full-record duplicates grouped by split',
            'projection': 'deterministic public education-to-education-number repair on generated rows; sampling distribution is pushforward; copula score remains approximate',
            'capital_zero_atoms': 'public integer support includes zero; copula is not claimed to preserve zero atom exactly',
            'numeric_model_scalers': 'client train fitted only',
            'fnlwgt_role': 'ordinary predictor, not survey expansion weight',
            'test_fitted_transformations': False,
        },
        'target': {'alpha_definition': 'client training count divided by total client training count',
                   'primary_reference': 'sum_i alpha_i times own official-test client empirical query mean',
                   'secondary_reference': 'ordinary unweighted pooled official-test empirical query mean',
                   'weights_do_not_redefine_target': True,
                   'empty_alpha_positive_test_client': 'cell primary endpoint unsupported, no redistribution'},
        'partitions': {'k': [5,10], 'kinds': ['age','age_education','label_skew'],
            'severity': .8, 'master_seeds': [404,505],
            'assignment_fit': 'train only; same fitted rule applied to tune/calibration/validation/official test',
            'test_label_routing': 'label-skew benchmark assignment may use test Y in privileged evaluator; no prediction-time deployment claim',
            'train_tune_cal_validation': 'official Adult training source only, duplicate quarantine and fixed split function',
            'source_archive_sha256': sha256(ROOT / 'data/raw/adult.zip')},
        'main_weight_rule': {'name': 'size', 'formula': 'w=alpha',
            'allocation': 'exact m largest-remainder client row counts; deterministic stable tie order'},
        'challenger': {'name': 'constrained_query_minimax',
            'objective': 'minimum finite-pilot maximum absolute calibration query residual',
            'inputs': 'independent 1500-row/client model pilot H, unnoised alpha-weighted aggregate real calibration query means, public alpha',
            'delta_l1': .25, 'floor_ratio': .5,
            'solver': 'SciPy HiGHS LP, certificate required; failure remains failure',
            'nonprivate_summary_release': True},
        'primary_workload': {'name': 'Q_primary_v2', 'path': relative_hash(WORKLOAD),
            'metric': 'max absolute empirical query difference; alpha-standardized reference',
            'actual_queries': len(primary.queries)},
        'audit_workload': {'name': 'viewed_development_audit', 'path': relative_hash(WORKLOAD),
            'actual_queries': len(audit.queries),
            'viewed_during_development': True,
            'confirmation_use': 'registered descriptive secondary endpoint, never reselect method'},
        'synthetic_draws': {'rows': 10000, 'repeats': 5,
            'allocation': 'largest_remainder', 'draw_seed_formula': 'master seed + 4200 + replicate',
            'same_fitted_models_across_weight_methods': True,
            'same_draw_seed_per_method_and_replicate': True},
        'random_substreams': {'local_fit': 'master seed + 31*client + grid_index',
            'local_tune_draw': 'master seed + 31*client + 100 + grid_index',
            'weight_pilot': 'master seed + 900 + client, 1500 rows/client',
            'main_draw': 'master seed + 4200 + replicate',
            'utility_synthetic_train_tune_cal': ['master seed + 9000', 'master seed + 10000', 'master seed + 11000'],
            'utility_fit': 'master seed + 12000',
            'conditional_support_pilot': 'master seed + 13000',
            'conditional_proposals': 'master seed + 14000 + 100*condition_index + proposal_batch_index',
            'private_histogram_noise': 'OS entropy, never public deterministic seed'},
        'conditional_policy': {'default': 'direct teacher rejection from selected size-weighted mixture',
            'conditions': [q.__dict__ for q in CONDITIONS],
            'valid_new_requests': 'structured finite Boolean combinations of documented categorical sets/numeric integer intervals validated against public schema; impossible requests error before sampling; support-domain enumeration capped at 100000 assignments',
            'pilot_rows': 30000, 'minimum_matching_rows': 300, 'minimum_pilot_mass': .01,
            'target_accepted_rows': 1000, 'maximum_proposals': 200000,
            'support_access': 'independent generated pilot only, no held-out real count or label',
            'student_role': 'separately labelled development alternative; no arbitrary-condition generalization claim',
            'support_claim': 'operational heuristic, not certified true condition probability'},
        'predictive_policy': {'learners': ['logistic','extra_trees'],
            'logistic_C_grid': [.1, 1., 10.], 'logistic_solver': 'liblinear',
            'extra_trees_min_leaf_grid': [3,8], 'extra_trees_estimators': 120,
            'grid_selection': 'lowest source-specific tune Brier, smaller parameter tie',
            'calibration': 'Platt sigmoid on independent source-specific calibration set; no assessment/official test calibration',
            'tstr_train_tune_cal_rows': [10000,2000,2000],
            'trtr_roles': ['real train','real tune','real calibration'],
            'test_population': 'same official people for all paired predictions, alpha-standardized row weights',
            'primary_proper_score': 'Brier', 'additional': ['log_loss','AUROC','AUPRC'],
            'probability_clip': 1e-6, 'group_auroc_minimum_per_class': 20,
            'joint_implied_copula_route': 'approximate score only; no exact projected conditional claim'},
        'baselines': [
            {'name': 'size', 'access': 'released models + public counts', 'privacy': 'nonprivate'},
            {'name': 'uniform', 'access': 'same released models', 'privacy': 'nonprivate'},
            {'name': 'constrained_query_minimax', 'access': 'released models + unnoised aggregate calibration query means', 'privacy': 'nonprivate'},
            {'name': 'TRTR', 'access': 'privileged real development', 'privacy': 'nonprivate'}],
        'metrics': {'primary': 'per-cell mean of five Q_primary_v2 query-max values; equal mean over two seeds per partition/K; overall equal mean over 12 cells',
            'paired_difference': 'constrained minus size, negative favours constrained',
            'practical_improvement_margin': .005,
            'material_primary_harm': 'candidate minus size above +0.005 in a partition/K slice',
            'representation': ['L1(w-alpha)','minimum w_i/alpha_i','observable subgroup prevalence','support coverage'],
            'secondary': ['viewed audit query max/MAE','column/dependency fidelity','Brier','log loss','AUROC','AUPRC','conditional feature error','support abstention','release bytes'],
            'uncertainty_unit': 'training/partition seed and fixed people; five draws quantify conditional synthetic sampling only; no independent-cohort p-value',
            'no_test_derived_reselection': True},
        'pilot_oracle': {'source': 'fixed independent 1500-row/client synthetic H',
            'target': 'real development validation aggregate query mean',
            'solver': 'finite-matrix HiGHS LP and certificate',
            'interpretation': 'empirical fixed-pilot benchmark, not population or nonlinear global optimum',
            'test_used_for_oracle': False},
        'software': {'code_hash': code_hash(), 'source_control': 'handoff copy without .git metadata; canonical btp source hash plus individual script/config hashes',
            'confirmation_runner_sha256': sha256(ROOT / 'scripts/run_adult_confirmation.py'),
            'secondary_runner_sha256': sha256(ROOT / 'scripts/report_adult_confirmation_secondary.py'),
            'dependency_freeze_sha256': sha256(DEPENDENCIES)},
        'inputs': inputs,
        'confirmation_commands': [
            '.venv/bin/python scripts/run_adult_confirmation.py --freeze SELECTION_FROZEN.json --preflight',
            '.venv/bin/python scripts/run_adult_confirmation.py --freeze SELECTION_FROZEN.json --run --max-cells 12',
            '.venv/bin/python scripts/report_adult_confirmation_secondary.py --freeze SELECTION_FROZEN.json --run --max-cells 12'],
        'reporting_change_policy': 'tables, plots, typo corrections and transparent uncertainty descriptions may change after confirmation without altering endpoints or scoring code',
        'code_fix_invalidation_policy': 'preserve first scored outputs and test-read timestamp; repair only implementation defects without scientific retuning; label corrected confirmation; new model selection invalidates untouched Adult confirmation',
        'alternatives_considered': [
            {'family': 'chow_liu', 'reason': 'higher registered mean primary validation query max than copula'},
            {'family': 'mixed_gmm', 'reason': 'higher registered mean primary validation query max than copula'},
            {'weighting': 'constrained_query_minimax', 'reason': 'no registered practical improvement across Adult development slices; retained comparator, not selected main rule'},
            {'weighting': 'unconstrained', 'reason': 'violates registered target-mass representation budget in apparent gain slices'}],
        'known_limitations': ['Adult assessment was viewed during developmental protocol repair; only the final generator comparison itself used validation',
            'official test reuses the same people across split seeds; no external independent-cohort confidence claim',
            'copula mixed-data scores are approximate and nominal order may matter',
            'main pipeline nonprivate and payloads can exceed raw-table bytes',
            'finite query workload omits some dependencies and cannot establish population TV',
            'FLAIM/Private-PGM development references have different trust or access contracts',
            'support pilot is heuristic and conditional teacher uses rejection cost'],
        'assessment_informed_history': 'Earlier assessment diagnostics informed public education projection, zero-atom handling, workload v2 and support/representation policies; these are exploratory design adaptations. Final family selection uses only fixed development validation rows and saved compatible models.',
        'confirmation_seeds': [404,505],
        'test_used_for_selection': False,
        'confirmation_seeds_used_for_selection': False,
        'global_freeze_complete': True,
        'assessment_informed_design': True,
        'main_pipeline_private': False,
    }
    payload = canonical_bytes(freeze)
    FREEZE.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    FREEZE.with_suffix(FREEZE.suffix+'.sha256').write_text(digest+'\n', encoding='ascii')
    immutable = ROOT / 'freezes/SELECTION_FROZEN_20261025.json'
    immutable.parent.mkdir(parents=True, exist_ok=True)
    immutable.write_bytes(payload)
    immutable.with_suffix(immutable.suffix+'.sha256').write_text(digest+'\n', encoding='ascii')
    validate_freeze(FREEZE, ROOT, code_hash())
    print(json.dumps({'freeze_sha256': digest, 'selected_generator': 'copula',
                      'official_test_read': False}))


if __name__ == '__main__':
    main()
