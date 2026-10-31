"""Inventory historical/current BTP cells without conflating their protocols."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results'


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def category(root: str) -> str:
    if root == 'adult_confirmation_20261025':
        return 'frozen_official_confirmation'
    if root == 'external_bank_20261025':
        return 'prospectively_frozen_external_assessment'
    if root == 'ec2_projected_v2_deterministic_20261024':
        return 'corrected_projected_adult_development_core'
    if root == 'representation_constrained_projected_v2_deterministic_20261024':
        return 'corrected_projected_adult_development_comparator'
    if root in ('severity_fixed_quantity_20261025',):
        return 'controlled_development_mechanism'
    if 'projected' in root or 'public_atom' in root:
        return 'development_secondary_or_ablation'
    if 'genuity' in root:
        return 'historical_protocol_mismatched_genuity'
    if 'smoke' in root or 'pilot' in root:
        return 'historical_software_validation_or_pilot'
    return 'historical_exploratory_development'


def status(cell: Path) -> tuple[str, list[str]]:
    failures = sorted(str(p.relative_to(cell)) for p in cell.glob('*failure*.json'))
    failures += sorted(str(p.relative_to(cell)) for p in cell.glob('*unsupported*.json'))
    if (cell / 'failure.json').exists():
        return 'failed', failures
    if (cell / 'unsupported.json').exists():
        return 'unsupported', failures
    if (cell / 'complete.json').exists():
        return 'complete', failures
    if (cell / 'exp02_complete.json').exists() and (cell / 'exp01_complete.json').exists():
        return 'registered_exp01_02_complete', failures
    if (cell / 'metrics.csv').exists() and (cell / 'weight_fits.json').exists():
        return 'registered_comparator_complete', failures
    if (cell / 'exp12_complete.json').exists():
        return 'starter_12_markers_complete_scope_unverified', failures
    if (cell / 'exp01_complete.json').exists() or (cell / 'exp01_test.csv').exists():
        return 'partial_or_exp01_complete', failures
    if (cell / 'configuration.json').exists() or (cell / 'metrics.csv').exists():
        return 'attempted_status_requires_read', failures
    return 'directory_no_cell_marker', failures


def main() -> None:
    rows = []
    for root in sorted(SOURCE.iterdir()):
        if not root.is_dir():
            continue
        for cell in sorted(root.iterdir()):
            if not cell.is_dir():
                continue
            config_path = cell / 'configuration.json'
            config = json.loads(config_path.read_text()) if config_path.exists() else {}
            state, failures = status(cell)
            rows.append({'root': str(root.relative_to(ROOT)),
                'cell': str(cell.relative_to(ROOT)),
                'category': category(root.name), 'status': state,
                'failure_files': json.dumps(failures),
                'configuration_sha256': sha(config_path),
                'code_hash': config.get('code_hash', config.get('source_code_hash')),
                'generator': config.get('generator'),
                'partition': config.get('partition'),
                'k': config.get('k'), 'seed': config.get('seed'),
                'reference_role': config.get('reference_role'),
                'freeze_sha256': config.get('freeze_sha256'),
                'configuration_path': str(config_path.relative_to(ROOT)) if config_path.exists() else None})
    reference_root = ROOT / 'reports/published_references'
    if reference_root.exists():
        for cell in sorted(reference_root.iterdir()):
            if not cell.is_dir() or not cell.name.startswith(('pgm_', 'flaim_')):
                continue
            flavor = 'pgm' if cell.name.startswith('pgm_') else 'flaim'
            marker = cell / f'{flavor}_complete.json'
            config_path = cell / ('configuration.json' if flavor == 'flaim' else 'measurement_package.json')
            rows.append({'root': 'reports/published_references', 'cell': str(cell.relative_to(ROOT)),
                'category': f'published_reference_{flavor}_development',
                'status': 'complete' if marker.exists() else 'failed_or_incomplete',
                'failure_files': '[]', 'configuration_sha256': sha(config_path),
                'code_hash': None, 'generator': flavor, 'partition': None,
                'k': None, 'seed': None, 'reference_role': 'development_assessment',
                'freeze_sha256': None,
                'configuration_path': str(config_path.relative_to(ROOT)) if config_path.exists() else None})
    frame = pd.DataFrame(rows)
    frame.to_csv(ROOT / 'ALL_RUNS_INDEX.csv', index=False)
    (ROOT / 'ALL_RUNS_INDEX.json').write_text(json.dumps(rows, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'directories': len(frame), 'by_category': frame.category.value_counts().to_dict(),
                      'by_status': frame.status.value_counts().to_dict()}))


if __name__ == '__main__':
    main()
