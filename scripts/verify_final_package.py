"""Clean-room-style saved-artifact and one-draw reproducibility check."""
from __future__ import annotations

import hashlib
import json
import pickle
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.evaluation import sample_mixture
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP
from btp.run import code_hash
from scripts.freeze_gate import validate_freeze, sha256


def check() -> dict:
    freeze_path = ROOT / 'SELECTION_FROZEN.json'
    freeze = validate_freeze(freeze_path, ROOT, code_hash())
    digest = sha256(freeze_path)
    first = json.loads((ROOT / 'reports/confirmation/FIRST_OFFICIAL_TEST_READ.json').read_text())
    if first['freeze_sha256'] != digest or first['first_access_at_utc'] <= freeze['created_at_utc']:
        raise ValueError('Test-read timestamp/freeze relation invalid')
    cells = sorted((ROOT / 'results/adult_confirmation_20261025').glob('*/complete.json'))
    if len(cells) != 12:
        raise ValueError('Expected exactly twelve terminal primary confirmation cells')
    for marker in cells:
        cell = marker.parent
        record = json.loads(marker.read_text())
        if record['freeze_sha256'] != digest:
            raise ValueError('Mixed confirmation freeze')
        for name, key in [('primary_draw_metrics.csv', 'primary_metrics_sha256'),
                          ('per_query_answers.csv', 'per_query_sha256'),
                          ('draw_manifest.json', 'draw_manifest_sha256')]:
            if sha256(cell / name) != record[key]:
                raise ValueError(f'Confirmation artifact hash mismatch: {cell}/{name}')
        for marker_name, file_name, key in (
            ('utility_complete.json','utility_predictions.csv.gz','predictions_sha256'),
            ('conditional_complete.json','conditional_metrics.csv','metrics_sha256')):
            status = json.loads((cell / marker_name).read_text())
            if sha256(cell / file_name) != status[key]:
                raise ValueError(f'Secondary hash mismatch: {cell}/{file_name}')
        for draw in json.loads((cell / 'draw_manifest.json').read_text()):
            if sha256(cell / draw['file']) != draw['sha256']:
                raise ValueError(f'Synthetic draw hash mismatch: {cell}/{draw["file"]}')
    cell = next(marker.parent for marker in cells if marker.parent.name == 'copula_age_k5_s404')
    cfg = json.loads((cell / 'configuration.json').read_text())
    k = cfg['k']
    models = [pickle.loads((cell / f'client_{i}.pkl').read_bytes()) for i in range(k)]
    weights = json.loads((cell / 'weights.json').read_text())['weights']
    seed = cfg['seed'] + 4200
    synth, counts = sample_mixture(models, np.asarray(weights['size'], float), 10000, seed)
    saved = next(row for row in json.loads((cell / 'draw_manifest.json').read_text())
                 if row['method'] == 'size' and row['replicate'] == 0)
    if counts.tolist() != saved['allocation_counts']:
        raise ValueError('Largest-remainder allocation not reproduced')
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / saved['file']
        synth.to_csv(output, index=False, compression={'method': 'gzip', 'mtime': 0})
        if sha256(output) != saved['sha256']:
            raise ValueError('Small synthetic draw is not byte reproducible')
    if not synth.income.isin(('<=50K','>50K')).all():
        raise ValueError('Invalid income in reproduced synthetic draw')
    mapped = synth.education.map(PUBLIC_EDUCATION_NUMBER_MAP)
    if not synth.loc[mapped.notna(), 'education-num'].eq(mapped[mapped.notna()]).all():
        raise ValueError('Projected education relation violated')
    metrics = pd.read_csv(cell / 'primary_draw_metrics.csv')
    answers = pd.read_csv(cell / 'per_query_answers.csv')
    size0 = metrics[(metrics.method == 'size') & (metrics.replicate == 0)].iloc[0]
    qmax = answers[(answers.method == 'size') & (answers.replicate == 0)
                   & (answers.workload == 'primary_v2')].absolute_error.max()
    if abs(float(size0.query_linf)-float(qmax)) > 1e-12:
        raise ValueError('Saved table does not reproduce the named worst query')
    summary = json.loads((ROOT / 'reports/final_build/summary.json').read_text())
    if summary['confirmation']['completed_primary_cells'] != 12 or summary['confirmation']['utility_cells'] != 12:
        raise ValueError('Final report summary incomplete')
    return {'status': 'verified', 'freeze_sha256': digest,
            'primary_cells': 12, 'secondary_cells': 12,
            'reproduced_draw_sha256': saved['sha256'],
            'reproduced_primary_query_max': float(qmax)}


if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True))
