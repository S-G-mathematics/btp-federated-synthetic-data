"""Fail-closed, fixed-procedure Adult official-test confirmation.

This is the only executable official-test path. It refuses to read any Adult
split until the complete canonical campaign freeze and input hashes validate.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pickle
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, build_partition_rule, prepare_splits
from btp.evaluation import empirical_metrics, sample_mixture, weighted_reference, CONDITIONS
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from btp.run import code_hash, tune_client
from scripts.freeze_gate import validate_freeze, sha256
from scripts.representation_constrained import constrained_query_minimax

OUT = ROOT / 'results/adult_confirmation_20261025'
REPORT = ROOT / 'reports/confirmation'
KINDS = ('age', 'age_education', 'label_skew')
KS = (5, 10)
SEEDS = (404, 505)
PROFILE = {'smoke': False, 'severity': .8, 'pilot_samples': 1500,
           'tune_samples': 1000, 'structural_projection': True}
M, REPEATS = 10000, 5


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str) + '\n')
    temp.replace(path)


def check_capacity(resources: dict) -> None:
    mem = Path('/proc/meminfo').read_text()
    avail = next(int(line.split()[1])*1024 for line in mem.splitlines()
                 if line.startswith('MemAvailable:'))
    if avail < resources['minimum_available_ram_gib']*2**30:
        raise RuntimeError('Available RAM below shared minimum')
    if shutil.disk_usage(ROOT).free < resources['minimum_free_disk_gib']*2**30:
        raise RuntimeError('Free disk below shared minimum')


def run_cell(freeze: dict, freeze_sha: str, kind: str, k: int, seed: int) -> None:
    started = time.monotonic()
    cell = OUT / f"{freeze['selected_generator']}_{kind}_k{k}_s{seed}"
    cell.mkdir(parents=True, exist_ok=True)
    if (cell / 'complete.json').exists():
        complete = json.loads((cell / 'complete.json').read_text())
        if complete['freeze_sha256'] != freeze_sha:
            raise ValueError('Prior confirmation cell has different freeze')
        print(cell.name, 'compatible complete cell retained', flush=True)
        return
    if (cell / 'configuration.json').exists():
        existing = json.loads((cell / 'configuration.json').read_text())
        if existing['freeze_sha256'] != freeze_sha:
            raise ValueError('Partial confirmation cell has different freeze')
    else:
        write_json(cell / 'configuration.json', {
            'status': 'FROZEN', 'reference_role': 'official_adult_test_confirmation',
            'generator': freeze['selected_generator'], 'partition': kind,
            'k': k, 'seed': seed, 'freeze_sha256': freeze_sha,
            'source_code_hash': code_hash(), 'runner_sha256': sha256(Path(__file__)),
            'raw_archive_sha256': sha256(ROOT / 'data/raw/adult.zip'),
            'profile': PROFILE, 'created_at_utc': utc(),
            'hardware': {'hostname': platform.node(), 'platform': platform.platform(),
                         'python': sys.version}})
    write_json(cell / 'state.json', {'state': 'RUNNING', 'started_at_utc': utc(),
                                    'freeze_sha256': freeze_sha})
    schema = public_schema()
    workload, audit = projected_workloads_v2(schema)
    first_access = REPORT / 'FIRST_OFFICIAL_TEST_READ.json'
    if not first_access.exists():
        write_json(first_access, {'first_access_at_utc': utc(),
                    'cause': 'scripts/run_adult_confirmation.py after accepted global freeze',
                    'freeze_sha256': freeze_sha, 'first_cell': cell.name})
    splits = prepare_splits(ROOT / 'data/raw', seed)
    rule = build_partition_rule(splits['train'], k, kind, seed, PROFILE['severity'])
    parts = {name: [frame.loc[rule.assign(frame) == i] for i in range(k)]
             for name, frame in splits.items() if name != 'quarantine'}
    train_counts = np.asarray([len(p) for p in parts['train']])
    alpha = train_counts / train_counts.sum()
    split_counts = {s: [len(p) for p in col] for s, col in parts.items()}
    manifest = [{'row_id': str(rid), 'split': name, 'client': int(client)}
                for name, frame in splits.items() if name != 'quarantine'
                for rid, client in zip(frame.index, rule.assign(frame))]
    pd.DataFrame(manifest).to_csv(cell / 'partition_manifest.csv', index=False)
    write_json(cell / 'partition.json', {'alpha': alpha.tolist(),
        'training_counts': train_counts.tolist(), 'split_client_counts': split_counts,
        'rule': rule.__dict__, 'label_skew_test_assignment_uses_label_in_privileged_evaluator':
            kind == 'label_skew',
        'target': 'fixed training-mass alpha; test query means standardized by client'})
    if min(map(len, parts['train'])) < 2 or min(map(len, parts['tune'])) < 2 or min(map(len, parts['calibration'])) < 2:
        write_json(cell / 'unsupported.json', {'reason': 'tiny train/tune/calibration client',
                                               'counts': split_counts})
        write_json(cell / 'state.json', {'state': 'UNSUPPORTED', 'freeze_sha256': freeze_sha})
        return
    if any(alpha[i] > 0 and len(parts['test'][i]) == 0 for i in range(k)):
        write_json(cell / 'unsupported.json', {'reason': 'alpha-positive client has no official-test reference rows',
                                               'counts': split_counts})
        write_json(cell / 'state.json', {'state': 'UNSUPPORTED', 'freeze_sha256': freeze_sha})
        return
    models = []
    selected = []
    for i in range(k):
        checkpoint = cell / f'client_{i}.pkl'
        tune_path = cell / f'tuning_{i}.json'
        if checkpoint.exists() and tune_path.exists():
            model = pickle.loads(checkpoint.read_bytes())
            tuning = json.loads(tune_path.read_text())
            setting = tuning['selected']
        else:
            model, setting, trials = tune_client(freeze['selected_generator'],
                parts['train'][i], parts['tune'][i], workload, schema,
                seed + 31*i, PROFILE)
            checkpoint.write_bytes(pickle.dumps(model, protocol=5))
            write_json(tune_path, {'selected': setting, 'trials': trials,
                                   'used_split': 'train/local_tune_only'})
        models.append(model)
        selected.append(setting)
        if time.monotonic()-started > 3600:
            raise TimeoutError('One-hour confirmation cell cap during local fits')
    write_json(cell / 'model_manifest.json', {'selected_settings': selected,
        'client_checkpoint_sha256': [sha256(cell / f'client_{i}.pkl') for i in range(k)]})
    H = np.column_stack([workload.mean(model.sample(1500, seed+900+i))
                         for i, model in enumerate(models)])
    b_cal = weighted_reference(parts['calibration'], workload, alpha)
    np.savez_compressed(cell / 'permitted_summary.npz', H=H, b_calibration=b_cal, alpha=alpha)
    constrained, certificate = constrained_query_minimax(H, b_cal, alpha, .25, .5)
    weights = {'size': alpha, 'uniform': np.ones(k)/k, 'constrained': constrained}
    b_val = weighted_reference(parts['validation'], workload, alpha)
    oracle, oracle_certificate = constrained_query_minimax(H, b_val, alpha, 2., 0.)
    write_json(cell / 'weights.json', {
        'weights': {name: w.tolist() for name, w in weights.items()},
        'constrained_certificate': certificate,
        'finite_pilot_validation_lp_oracle': {'weights': oracle.tolist(), **oracle_certificate},
        'pilot_rows_per_client': 1500,
        'pilot_access': 'released models and aggregate unnoised calibration means only',
        'validation_oracle_access': 'privileged, diagnostic only, not method selection'})
    real_primary = weighted_reference(parts['test'], workload, alpha)
    real_audit = weighted_reference(parts['test'], audit, alpha)
    pooled_primary = workload.mean(splits['test'])
    pooled_audit = audit.mean(splits['test'])
    rows, answers, draw_manifest = [], [], []
    for method, weight in weights.items():
        for rep in range(REPEATS):
            draw_seed = seed+4200+rep
            synth, allocation = sample_mixture(models, weight, M, draw_seed)
            if len(synth) != M or not synth.income.isin(['<=50K', '>50K']).all():
                raise ValueError('Invalid confirmation synthetic dataset')
            metrics = empirical_metrics(parts['test'], synth, workload, audit, alpha)
            q = workload.mean(synth)
            a = audit.mean(synth)
            path = cell / f'synthetic_{method}_draw{rep}.csv.gz'
            synth.to_csv(path, index=False, compression={'method': 'gzip', 'mtime': 0})
            draw_manifest.append({'method': method, 'replicate': rep, 'draw_seed': draw_seed,
                'file': path.name, 'sha256': sha256(path), 'allocation_counts': allocation.tolist()})
            rows.append({'method': method, 'replicate': rep, 'draw_seed': draw_seed,
                'partition': kind, 'k': k, 'seed': seed,
                'weight_l1': float(np.abs(weight-alpha).sum()),
                'minimum_weight_alpha_ratio': float(np.min(weight/alpha)),
                'allocation_counts': json.dumps(allocation.tolist()),
                'pooled_primary_query_linf_secondary': float(np.abs(q-pooled_primary).max()),
                **metrics})
            for query, real, pooled, syn in zip(workload.queries, real_primary, pooled_primary, q):
                answers.append({'method': method, 'replicate': rep, 'workload': 'primary_v2',
                    'query': query.name, 'real_alpha': float(real), 'real_pooled_secondary': float(pooled),
                    'synthetic': float(syn), 'absolute_error': float(abs(real-syn))})
            for query, real, pooled, syn in zip(audit.queries, real_audit, pooled_audit, a):
                answers.append({'method': method, 'replicate': rep, 'workload': 'viewed_audit',
                    'query': query.name, 'real_alpha': float(real), 'real_pooled_secondary': float(pooled),
                    'synthetic': float(syn), 'absolute_error': float(abs(real-syn))})
        if time.monotonic()-started > 3600:
            raise TimeoutError('One-hour confirmation cell cap during draws')
    pd.DataFrame(rows).to_csv(cell / 'primary_draw_metrics.csv', index=False)
    pd.DataFrame(answers).to_csv(cell / 'per_query_answers.csv', index=False)
    write_json(cell / 'draw_manifest.json', draw_manifest)
    write_json(cell / 'complete.json', {'status': 'complete', 'freeze_sha256': freeze_sha,
        'finished_at_utc': utc(), 'elapsed_seconds': time.monotonic()-started,
        'primary_metrics_sha256': sha256(cell / 'primary_draw_metrics.csv'),
        'per_query_sha256': sha256(cell / 'per_query_answers.csv'),
        'draw_manifest_sha256': sha256(cell / 'draw_manifest.json')})
    write_json(cell / 'state.json', {'state': 'COMPLETE', 'freeze_sha256': freeze_sha,
                                   'finished_at_utc': utc()})
    print(cell.name, 'complete', flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--preflight', action='store_true')
    ap.add_argument('--max-cells', type=int, default=12)
    args = ap.parse_args()
    if not (args.run or args.preflight):
        ap.error('Specify --preflight or --run')
    freeze = validate_freeze(args.freeze, ROOT, code_hash())
    freeze_sha = hashlib.sha256(args.freeze.read_bytes()).hexdigest()
    if freeze['selected_generator'] != 'copula':
        raise ValueError('Installed Adult validation decision selects copula; freeze disagrees')
    if args.preflight:
        print(json.dumps({'gate': 'accepted', 'freeze_sha256': freeze_sha,
                          'official_test_read': False}))
        return
    resource = yaml.safe_load((ROOT / 'configs/resources.yaml').read_text())
    lease = Path(os.path.expanduser(resource['shared_compute_lease']))
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    with lease.open('a+') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = time.monotonic()
        completed = 0
        for kind in KINDS:
            for k in KS:
                for seed in SEEDS:
                    if completed >= args.max_cells:
                        return
                    if time.monotonic()-started > resource['campaign_wall_seconds']:
                        raise TimeoutError('Two-hour confirmation invocation cap')
                    check_capacity(resource)
                    try:
                        run_cell(freeze, freeze_sha, kind, k, seed)
                    except Exception:
                        cell = OUT / f"{freeze['selected_generator']}_{kind}_k{k}_s{seed}"
                        write_json(cell / 'failure.json', {'status': 'failed',
                            'failed_at_utc': utc(), 'traceback': traceback.format_exc(),
                            'freeze_sha256': freeze_sha})
                        write_json(cell / 'state.json', {'state': 'FAILED', 'freeze_sha256': freeze_sha})
                        raise
                    completed += 1


if __name__ == '__main__':
    main()
