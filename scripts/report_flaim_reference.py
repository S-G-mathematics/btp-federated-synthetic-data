"""Privileged empirical scoring of fixed FLAIM DP-reference draws."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.evaluation import empirical_metrics, weighted_reference
from btp.privacy import public_schema
from btp.projected_workload import projected_workloads_v2
from scripts.representation_constrained import reference_parts
from scripts.report_pgm_reference import decode

OUT = ROOT / 'reports/published_references'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((OUT / 'pgm_cell_manifest.json').read_text())
    workload, audit = projected_workloads_v2(public_schema())
    rows, answers, statuses = [], [], []
    for entry in manifest['cells']:
        label = entry['name'].replace('pgm_', 'flaim_')
        cell = OUT / label
        marker = cell / 'flaim_complete.json'
        if not marker.exists():
            statuses.append({'cell': label, 'status': 'failed_or_missing'})
            continue
        complete = json.loads(marker.read_text())
        if sha(cell / 'model_flaim.pkl') != complete['model_sha256']:
            raise ValueError('FLAIM checkpoint hash mismatch')
        package = json.loads((OUT / entry['name'] / 'measurement_package.json').read_text())
        source = ROOT / entry['source_cell']
        cfg = json.loads((source / 'configuration.json').read_text())
        alpha = np.asarray(json.loads((source / 'partition.json').read_text())['alpha'], float)
        parts = reference_parts(source, cfg, alpha)
        real = weighted_reference(parts['test'], workload, alpha)
        pooled = workload.mean(pd.concat(parts['test']))
        baseline = pd.read_csv(source / 'exp01_test.csv')
        size = baseline.loc[baseline.method == 'size'].sort_values('replicate')
        if len(size) != 5:
            raise ValueError('Missing matched size baseline')
        for item in complete['draws']:
            draw = cell / item['path']
            if sha(draw) != item['sha256']:
                raise ValueError('FLAIM discrete draw hash mismatch')
            synth, preprojection_violation = decode(package, draw, item['seed'])
            metrics = empirical_metrics(parts['test'], synth, workload, audit, alpha)
            q = workload.mean(synth)
            rep = item['replicate']
            rows.append({'cell': label, 'partition': cfg['partition'], 'k': cfg['k'],
                         'seed': cfg['seed'], 'replicate': rep, 'draw_seed': item['seed'],
                         'privacy': 'authors_FLAIM_distributed_accounting_epsilon4_delta1e-6_fixed_membership_only',
                         'access': 'client_raw_train_rows_interactive_noisy_marginals',
                         'access_matched_to_size': False,
                         'accountant_epsilon_reported': complete['epsilon_spent_reported'],
                         'preprojection_education_relation_violation': preprojection_violation,
                         'size_baseline_query_linf_same_rep': float(size.iloc[rep].query_linf),
                         'flaim_minus_size': metrics['query_linf']-float(size.iloc[rep].query_linf),
                         'pooled_reference_query_linf_secondary': float(np.abs(q-pooled).max()),
                         **metrics})
            if rep == 0:
                synth.to_csv(cell / 'decoded_projected_draw0.csv.gz', index=False,
                             compression={'method': 'gzip', 'mtime': 0})
            for query, real_value, pooled_value, syn_value in zip(workload.queries, real, pooled, q):
                answers.append({'cell': label, 'replicate': rep, 'query': query.name,
                                'real_alpha': float(real_value),
                                'real_pooled_secondary': float(pooled_value),
                                'synthetic': float(syn_value),
                                'absolute_error': float(abs(real_value-syn_value))})
        statuses.append({'cell': label, 'status': 'complete',
                         'accountant_epsilon_reported': complete['epsilon_spent_reported']})
    pd.DataFrame(statuses).to_csv(OUT / 'flaim_status.csv', index=False)
    if rows:
        frame = pd.DataFrame(rows)
        frame.to_csv(OUT / 'flaim_assessment_draws.csv', index=False)
        pd.DataFrame(answers).to_csv(OUT / 'flaim_per_query.csv', index=False)
        cells = frame.groupby(['cell', 'partition', 'k', 'seed'], as_index=False).agg(
            flaim_query_linf_mean=('query_linf', 'mean'),
            size_query_linf_mean=('size_baseline_query_linf_same_rep', 'mean'),
            flaim_minus_size_mean=('flaim_minus_size', 'mean'),
            preprojection_relation_violation_mean=('preprojection_education_relation_violation', 'mean'))
        cells.to_csv(OUT / 'flaim_cell_means.csv', index=False)
    print(json.dumps({'complete_cells': len(rows)//5, 'planned_cells': len(manifest['cells'])}))


if __name__ == '__main__':
    main()
