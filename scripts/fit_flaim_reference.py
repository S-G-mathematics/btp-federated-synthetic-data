"""Bounded protocol-mismatched FLAIM DP reference on fixed Adult client rows.

Run only in the isolated Python 3.9 FLAIM environment, under the shared lease.
This adapter passes real train partitions to the published client-side algorithm.
No held-out reference enters its fit. Private noise is not deterministically seeded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FLAIM = Path('/home/ubuntu/research-director/btp-reference-src-20261025/flaim')
sys.path.insert(0, str(FLAIM))
sys.path.insert(0, str(ROOT))
from synth_fl.generators import FederatedGeneratorConfig
from synth_fl.generators.federated.flaim import FLAIM as FLAIMGenerator
from synth_fl.utils.dataloaders import TabularDataset
from btp.data import ALL_COLUMNS, prepare_splits

OUT = ROOT / 'reports/published_references'
EPSILON, DELTA = 4.0, 1e-6
GLOBAL_ROUNDS = 4
ROWS, REPEATS = 10000, 5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(frame: pd.DataFrame, public_domain: dict) -> pd.DataFrame:
    out = {}
    for column in ALL_COLUMNS:
        spec = public_domain[column]
        if spec['kind'] == 'category':
            mapping = {str(v): i for i, v in enumerate(spec['values'])}
            unknown = mapping.get('__UNKNOWN__')
            vals = frame[column].astype(str).map(mapping)
            if vals.isna().any():
                if unknown is None:
                    raise ValueError(f'Unmapped category without public unknown code: {column}')
                vals = vals.fillna(unknown)
            out[column] = vals.to_numpy(dtype=int)
        else:
            intervals = np.asarray(spec['values'], dtype=int)
            x = np.asarray(frame[column], dtype=int)
            if np.any(x < intervals[0, 0]) or np.any(x > intervals[-1, 1]):
                raise ValueError(f'Train value outside public support: {column}')
            codes = np.searchsorted(intervals[:, 1], x, side='left')
            if np.any(x < intervals[codes, 0]):
                raise ValueError(f'Uncovered public interval: {column}')
            out[column] = codes
    return pd.DataFrame(out, columns=ALL_COLUMNS)


def one_cell(entry: dict) -> None:
    started = time.monotonic()
    source = ROOT / entry['source_cell']
    package_dir = OUT / entry['name']
    package = json.loads((package_dir / 'measurement_package.json').read_text())
    destination = OUT / entry['name'].replace('pgm_', 'flaim_')
    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / 'flaim_complete.json'
    if marker.exists():
        raise ValueError('FLAIM cell already complete; no repeated private release without accounting')
    spec = json.loads((source / 'configuration.json').read_text())
    splits = prepare_splits(ROOT / 'data/raw', spec['seed'])
    train = splits['train']
    membership = pd.read_csv(source / 'partition_manifest.csv', dtype={'row_id': str})
    membership = membership[membership.split == 'train']
    joined = membership.join(train, on='row_id', validate='one_to_one')
    if joined[list(ALL_COLUMNS)].isna().any().any():
        raise ValueError('Missing joined train row')
    domain = package['domain']
    shape = {c: len(domain[c]['values']) for c in ALL_COLUMNS}
    clients = []
    counts = []
    for i in range(spec['k']):
        raw = joined[joined.client == i][list(ALL_COLUMNS)]
        counts.append(len(raw))
        clients.append(TabularDataset(f'btp_adult_client{i}', df=encoded(raw, domain),
                                      domain=shape, y='income', preprocess=False))
    if min(counts) < 2:
        raise ValueError('Tiny FLAIM client')
    workload = list(dict.fromkeys(tuple(m['clique']) for m in package['measurements']))
    cfg = FederatedGeneratorConfig(
        epsilon=EPSILON, delta=DELTA, num_clients=spec['k'],
        clients_per_round=1.0, global_rounds=GLOBAL_ROUNDS, local_rounds=1,
        accounting_method='distributed', aggregation_method='merge_all',
        selection_method='exp', gauss_budget_alloc=.5,
        pgm_train_iters=50, pgm_final_iters=500,
        normalize_measurements=True, init_method='',
        use_control_variates=False, skip_hetero_metrics=True,
        save_client_answer_cache=False, load_client_answer_cache=False,
        log_internal_metrics='', track_communication=True,
    )
    public_spec = {'reference_commit': '3e698da752b4af928a040f645f7e08fa306db4cd',
                   'autodp_commit': '06489ea485653909397937cf5e3c31d06a677ffe',
                   'epsilon': EPSILON, 'delta': DELTA, 'rounds': GLOBAL_ROUNDS,
                   'clients_per_round': 1.0, 'accounting_method': 'distributed',
                   'source_cell': entry['source_cell'], 'train_counts': counts,
                   'train_total': sum(counts), 'workload_cliques': workload,
                   'domain_shape': shape, 'source_config_sha256': sha(source / 'configuration.json'),
                   'source_membership_sha256': sha(source / 'partition_manifest.csv'),
                   'created_at_utc': datetime.now(timezone.utc).isoformat(),
                   'private_noise_seed_recorded': False,
                   'reference_access': 'client_raw_train_rows_and_interactive_noisy_marginal_rounds',
                   'access_matched_to_btp_summary_rule': False}
    config_path = destination / 'configuration.json'
    if not config_path.exists():
        config_path.write_text(json.dumps(public_spec, indent=2)+'\n')
    checkpoint = destination / 'model_flaim.pkl'
    fit_meta = destination / 'fit_metadata.json'
    if checkpoint.exists():
        # A private fit was already released to disk. Never rerun it merely
        # because deterministic postprocessing failed.
        model = pickle.loads(checkpoint.read_bytes())
        if fit_meta.exists():
            epsilon_spent = json.loads(fit_meta.read_text())['epsilon_spent_reported']
        else:
            log = ROOT / 'logs/flaim_age_education_k5_s101_20261025.log'
            matches = re.findall(r'Accountant eps ([0-9.eE+-]+)', log.read_text())
            if entry['name'] != 'pgm_age_education_k5_s101' or len(matches) != 1:
                raise ValueError('Existing private fit lacks auditable budget record')
            epsilon_spent = float(matches[0])
            fit_meta.write_text(json.dumps({'epsilon_spent_reported': epsilon_spent,
                'model_sha256': sha(checkpoint), 'recovered_from_log': str(log.relative_to(ROOT)),
                'recovery_reason': 'postfit synthetic_data tuple adapter failure'}, indent=2)+'\n')
    else:
        # FLAIM uses NumPy's process RNG. Seed it from private OS entropy, never
        # a serialised/public seed; public seeds apply only after fitting.
        np.random.seed(int.from_bytes(os.urandom(8), 'big') % (2**32))
        engine = FLAIMGenerator(cfg)
        engine.n = sum(counts)
        engine.num_clients = spec['k']
        engine.target = 'income'
        engine.synth_rows = ROWS
        for aim in engine.client_aims:
            aim.target = 'income'
        engine._generate(clients, workload)
        epsilon_spent = float(engine.accountant.get_eps())
        if not np.isfinite(epsilon_spent) or epsilon_spent > EPSILON + 1e-7:
            raise ValueError(f'FLAIM reported epsilon {epsilon_spent}, outside registered budget')
        model = engine.model
        checkpoint.write_bytes(pickle.dumps(model, protocol=5))
        fit_meta.write_text(json.dumps({'epsilon_spent_reported': epsilon_spent,
            'model_sha256': sha(checkpoint), 'recovered_from_log': None}, indent=2)+'\n')
    draws = []
    for rep in range(REPEATS):
        seed = spec['seed'] + 7600 + rep
        np.random.seed(seed)
        sampled = model.synthetic_data(rows=ROWS)[1]
        if sampled.shape != (ROWS, len(ALL_COLUMNS)):
            raise ValueError('Wrong FLAIM sample shape')
        file = destination / f'discrete_draw_{rep}.npz'
        np.savez_compressed(file, **{c: sampled[c].to_numpy(dtype=np.int16) for c in ALL_COLUMNS})
        draws.append({'replicate': rep, 'seed': seed, 'path': file.name, 'sha256': sha(file)})
    marker.write_text(json.dumps({'status': 'complete', 'source_cell': entry['source_cell'],
        'fit_seconds': time.monotonic()-started, 'epsilon_spent_reported': epsilon_spent,
        'delta_requested': DELTA, 'model_sha256': sha(checkpoint), 'draws': draws,
        'workload_cliques': len(workload), 'train_counts': counts}, indent=2)+'\n')
    print(json.dumps({'cell': entry['name'], 'status': 'complete',
                      'fit_seconds': time.monotonic()-started,
                      'epsilon_spent_reported': epsilon_spent}), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--cell', required=True)
    args = ap.parse_args()
    manifest = json.loads((OUT / 'pgm_cell_manifest.json').read_text())
    entries = [x for x in manifest['cells'] if x['name'] == args.cell]
    if len(entries) != 1:
        raise ValueError('Cell absent from registered four-cell manifest')
    one_cell(entries[0])


if __name__ == '__main__':
    main()
