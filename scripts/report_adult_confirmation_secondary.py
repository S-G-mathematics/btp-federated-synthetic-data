"""Frozen Adult confirmation utility and support-limited conditional endpoints."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import NUMERIC, PREDICTORS, ALL_COLUMNS, prepare_splits
from btp.evaluation import CONDITIONS, sample_mixture
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash, conditional_reference
from scripts.freeze_gate import validate_freeze, sha256

SOURCE = ROOT / 'results/adult_confirmation_20261025'
CLIP = 1e-6
METHODS = ('size', 'uniform', 'constrained')
LEARNERS = ('logistic', 'extra_trees')
TRAIN_ROWS, TUNE_ROWS, CAL_ROWS = 10000, 2000, 2000
CONDITION_PILOT = 30000
CONDITION_MIN_COUNT = 300
CONDITION_MIN_MASS = .01
CONDITION_ACCEPTED = 1000
CONDITION_MAX_PROPOSALS = 200000


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, indent=2, default=str, allow_nan=False)+'\n')
    tmp.replace(path)


def features(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[list(PREDICTORS)]


def y_values(frame: pd.DataFrame) -> np.ndarray:
    return (frame.income.to_numpy() == '>50K').astype(int)


def new_base(name: str, parameter: float, seed: int):
    numeric = [c for c in PREDICTORS if c in NUMERIC]
    categorical = [c for c in PREDICTORS if c not in NUMERIC]
    encoder = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('categorical', OneHotEncoder(handle_unknown='ignore', sparse_output=True), categorical)])
    model = (LogisticRegression(C=parameter, solver='liblinear', max_iter=600,
                                random_state=seed) if name == 'logistic'
             else ExtraTreesClassifier(n_estimators=120, min_samples_leaf=int(parameter),
                                       n_jobs=1, random_state=seed))
    return make_pipeline(encoder, model)


def fit(name: str, train: pd.DataFrame, tune: pd.DataFrame,
        calibration: pd.DataFrame, seed: int):
    if any(len(np.unique(y_values(part))) < 2 for part in (train, tune, calibration)):
        raise ValueError('Utility train/tune/calibration requires both income classes')
    grid = (.1, 1., 10.) if name == 'logistic' else (3., 8.)
    trials, winner = [], None
    for parameter in grid:
        base = new_base(name, parameter, seed)
        base.fit(features(train), y_values(train))
        p = np.clip(base.predict_proba(features(tune))[:, 1], CLIP, 1-CLIP)
        loss = float(brier_score_loss(y_values(tune), p))
        trials.append({'parameter': parameter, 'tune_brier': loss})
        if winner is None or (loss, parameter) < (winner[0], winner[1]):
            winner = (loss, parameter, base)
    base = winner[2]
    pc = np.clip(base.predict_proba(features(calibration))[:, 1], CLIP, 1-CLIP)
    logits = np.log(pc/(1-pc)).reshape(-1, 1)
    platt = LogisticRegression(C=1e6, solver='liblinear', max_iter=600,
                               random_state=seed+1).fit(logits, y_values(calibration))
    return base, platt, {'selected_parameter': winner[1], 'trials': trials,
        'calibration': 'Platt sigmoid on separate real or synthetic calibration rows',
        'train_rows': len(train), 'tune_rows': len(tune),
        'calibration_rows': len(calibration), 'clip': CLIP}


def predict(base, platt, frame: pd.DataFrame) -> np.ndarray:
    p = np.clip(base.predict_proba(features(frame))[:, 1], CLIP, 1-CLIP)
    logits = np.log(p/(1-p)).reshape(-1, 1)
    return np.clip(platt.predict_proba(logits)[:, 1], CLIP, 1-CLIP)


def metrics(y: np.ndarray, p: np.ndarray, weights: np.ndarray) -> dict:
    return {'brier': float(brier_score_loss(y, p, sample_weight=weights)),
            'log_loss': float(log_loss(y, p, sample_weight=weights, labels=[0,1])),
            'auroc': float(roc_auc_score(y, p, sample_weight=weights)) if len(np.unique(y)) == 2 else None,
            'auprc': float(average_precision_score(y, p, sample_weight=weights)) if len(np.unique(y)) == 2 else None}


def test_parts(cell: Path, seed: int, k: int) -> list[pd.DataFrame]:
    splits = prepare_splits(ROOT / 'data/raw', seed)
    manifest = pd.read_csv(cell / 'partition_manifest.csv', dtype={'row_id': str})
    test_rows = manifest.loc[manifest.split == 'test']
    joined = test_rows.join(splits['test'], on='row_id', validate='one_to_one')
    if joined[list(ALL_COLUMNS)].isna().any().any():
        raise ValueError('Confirmation manifest official-test join failed')
    joined = joined.set_index('row_id', verify_integrity=True)
    return [joined.loc[joined.client == i, list(ALL_COLUMNS)].copy() for i in range(k)]


def utility(cell: Path, models: list, weights: dict, groups: dict,
            test: list[pd.DataFrame], alpha: np.ndarray, seed: int) -> None:
    all_test = pd.concat(test)
    client_ids = np.concatenate([np.full(len(part), i) for i, part in enumerate(test)])
    row_weights = np.concatenate([np.full(len(part), alpha[i]/len(part)) for i, part in enumerate(test)])
    y = y_values(all_test)
    metric_rows, predictions, settings = [], [], {}
    for method in ('trtr_privileged', *METHODS):
        weight = weights.get(method)
        if method == 'trtr_privileged':
            train, tune, calibration = (pd.concat(groups[role]) for role in ('train', 'tune', 'calibration'))
        else:
            train, _ = sample_mixture(models, weight, TRAIN_ROWS, seed+9000)
            tune, _ = sample_mixture(models, weight, TUNE_ROWS, seed+10000)
            calibration, _ = sample_mixture(models, weight, CAL_ROWS, seed+11000)
        for learner in LEARNERS:
            fitted, calibrator, record = fit(learner, train, tune, calibration, seed+12000)
            p = predict(fitted, calibrator, all_test)
            metric_rows.append({'method': method, 'learner': learner, 'scope': 'global_alpha',
                'access': 'privileged_real_development' if method == 'trtr_privileged' else 'synthetic_released_models',
                'n_test': len(all_test), **metrics(y, p, row_weights)})
            predictions.extend({'row_id': str(rid), 'client': int(client), 'y': int(yi),
                'probability': float(pi), 'method': method, 'learner': learner,
                'alpha_row_weight': float(wi)}
                for rid, client, yi, pi, wi in zip(all_test.index, client_ids, y, p, row_weights))
            for i, part in enumerate(test):
                selected = client_ids == i
                yi, pi = y[selected], p[selected]
                if len(yi) == 0:
                    continue
                report = metrics(yi, pi, np.ones(len(yi))/len(yi))
                if min(np.sum(yi), np.sum(1-yi)) < 20:
                    report['auroc'] = None
                    report['auprc'] = None
                metric_rows.append({'method': method, 'learner': learner, 'scope': f'client_{i}',
                    'access': 'privileged_real_development' if method == 'trtr_privileged' else 'synthetic_released_models',
                    'n_test': len(yi), 'positives': int(np.sum(yi)), 'negatives': int(np.sum(1-yi)), **report})
            settings[f'{method}_{learner}'] = record
            (cell / f'utility_{method}_{learner}.pkl').write_bytes(
                pickle.dumps({'base': fitted, 'platt': calibrator}, protocol=5))
    pd.DataFrame(metric_rows).to_csv(cell / 'utility_metrics.csv', index=False)
    pd.DataFrame(predictions).to_csv(cell / 'utility_predictions.csv.gz', index=False,
                                     compression={'method': 'gzip', 'mtime': 0})
    write_json(cell / 'utility_settings.json', settings)
    write_json(cell / 'utility_complete.json', {'status': 'complete',
        'metrics_sha256': sha256(cell / 'utility_metrics.csv'),
        'predictions_sha256': sha256(cell / 'utility_predictions.csv.gz')})


def conditional(cell: Path, models: list, alpha: np.ndarray,
                test: list[pd.DataFrame], seed: int) -> None:
    primary, _ = projected_workloads_v2(public_schema())
    feature_queries = [q for q in primary.queries if all(term[0] != 'income' for term in q.terms)]
    from btp.evaluation import Workload
    feature_workload = Workload(feature_queries)
    pilot, _ = sample_mixture(models, alpha, CONDITION_PILOT, seed+13000)
    rows, answers = [], []
    for j, condition in enumerate(CONDITIONS):
        start = time.monotonic()
        mask = condition.evaluate(pilot).astype(bool)
        count = int(mask.sum())
        mass = count / CONDITION_PILOT
        row = {'condition': condition.name, 'support_pilot_count': count,
               'support_pilot_mass': mass, 'support_pilot_seed': seed+13000,
               'min_count': CONDITION_MIN_COUNT, 'min_mass': CONDITION_MIN_MASS,
               'requested_accepted': CONDITION_ACCEPTED,
               'maximum_proposals': CONDITION_MAX_PROPOSALS}
        if count < CONDITION_MIN_COUNT or mass < CONDITION_MIN_MASS:
            rows.append({**row, 'status': 'abstained_low_teacher_support',
                         'proposals': 0, 'accepted': 0, 'violation_rate': None,
                         'elapsed_seconds': time.monotonic()-start})
            continue
        accepted, proposals = [], 0
        while sum(len(part) for part in accepted) < CONDITION_ACCEPTED and proposals < CONDITION_MAX_PROPOSALS:
            batch_size = min(10000, CONDITION_MAX_PROPOSALS-proposals)
            batch, _ = sample_mixture(models, alpha, batch_size, seed+14000+100*j+proposals//10000)
            proposals += batch_size
            accepted.append(batch.loc[condition.evaluate(batch).astype(bool)])
        total = sum(len(part) for part in accepted)
        if total < CONDITION_ACCEPTED:
            rows.append({**row, 'status': 'abstained_proposal_cap',
                         'proposals': proposals, 'accepted': total,
                         'violation_rate': None, 'elapsed_seconds': time.monotonic()-start})
            continue
        frame = pd.concat(accepted, ignore_index=True).iloc[:CONDITION_ACCEPTED].copy()
        violation = float(1-condition.evaluate(frame).mean())
        if violation != 0:
            raise ValueError('Accepted conditional row violates registered request')
        reference, real_mass, real_count = conditional_reference(test, alpha, condition, feature_workload)
        if reference is None:
            status, error = 'unsupported_zero_real_reference', None
        else:
            error = np.abs(feature_workload.mean(frame)-reference)
            status = 'complete'
            for query, real, synth, gap in zip(feature_workload.queries, reference,
                                               feature_workload.mean(frame), error):
                answers.append({'condition': condition.name, 'query': query.name,
                    'real_alpha_conditional': float(real), 'synthetic': float(synth),
                    'absolute_error': float(gap)})
        path = cell / f'conditional_{condition.name}.csv.gz'
        frame.to_csv(path, index=False, compression={'method': 'gzip', 'mtime': 0})
        rows.append({**row, 'status': status, 'proposals': proposals,
            'accepted': len(frame), 'violation_rate': violation,
            'real_alpha_condition_mass': real_mass, 'real_condition_count': real_count,
            'feature_query_linf': None if error is None else float(error.max()),
            'feature_query_mae': None if error is None else float(error.mean()),
            'accepted_sha256': sha256(path), 'elapsed_seconds': time.monotonic()-start})
    pd.DataFrame(rows).to_csv(cell / 'conditional_metrics.csv', index=False)
    pd.DataFrame(answers).to_csv(cell / 'conditional_per_query.csv', index=False)
    write_json(cell / 'conditional_complete.json', {'status': 'complete',
        'metrics_sha256': sha256(cell / 'conditional_metrics.csv')})


def one_cell(cell: Path, freeze_sha: str) -> None:
    cfg = json.loads((cell / 'configuration.json').read_text())
    if cfg['freeze_sha256'] != freeze_sha or not (cell / 'complete.json').exists():
        raise ValueError('Secondary confirmation needs matching complete primary cell')
    k, seed = cfg['k'], cfg['seed']
    alpha = np.asarray(json.loads((cell / 'partition.json').read_text())['alpha'], float)
    weights = {key: np.asarray(value, float) for key, value in
               json.loads((cell / 'weights.json').read_text())['weights'].items()}
    models = [pickle.loads((cell / f'client_{i}.pkl').read_bytes()) for i in range(k)]
    if not (cell / 'utility_complete.json').exists():
        splits = prepare_splits(ROOT / 'data/raw', seed)
        manifest = pd.read_csv(cell / 'partition_manifest.csv', dtype={'row_id': str})
        development = pd.concat([splits[role] for role in ('train', 'tune', 'calibration')])
        joined = manifest.loc[manifest.split.isin(('train', 'tune', 'calibration'))].join(
            development, on='row_id', validate='one_to_one')
        groups = {role: [joined.loc[(joined.split == role) & (joined.client == i), list(ALL_COLUMNS)].copy()
                         for i in range(k)] for role in ('train', 'tune', 'calibration')}
        test = test_parts(cell, seed, k)
        utility(cell, models, weights, groups, test, alpha, seed)
    if not (cell / 'conditional_complete.json').exists():
        test = test_parts(cell, seed, k)
        conditional(cell, models, alpha, test, seed)
    print(cell.name, 'secondary complete', flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--run', action='store_true', required=True)
    ap.add_argument('--max-cells', type=int, default=12)
    args = ap.parse_args()
    freeze = validate_freeze(args.freeze, ROOT, code_hash())
    freeze_sha = hashlib.sha256(args.freeze.read_bytes()).hexdigest()
    resources = yaml.safe_load((ROOT / 'configs/resources.yaml').read_text())
    lease = Path(os.path.expanduser(resources['shared_compute_lease']))
    with lease.open('a+') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        started, completed = time.monotonic(), 0
        for cell in sorted(SOURCE.iterdir()):
            if not cell.is_dir() or not (cell / 'complete.json').exists():
                continue
            if completed >= args.max_cells:
                return
            if time.monotonic()-started > resources['campaign_wall_seconds']:
                raise TimeoutError('Secondary confirmation reached two-hour invocation cap')
            mem = Path('/proc/meminfo').read_text()
            avail = next(int(line.split()[1])*1024 for line in mem.splitlines() if line.startswith('MemAvailable:'))
            if avail < resources['minimum_available_ram_gib']*2**30 or shutil.disk_usage(ROOT).free < resources['minimum_free_disk_gib']*2**30:
                raise RuntimeError('Shared resource reserve breached')
            one_cell(cell, freeze_sha)
            completed += 1


if __name__ == '__main__':
    main()
