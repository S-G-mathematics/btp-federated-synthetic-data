"""Minimal import repairs to the pinned FLAIM source copy; never run on BTP code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ubuntu/research-director/btp-reference-src-20261025/flaim')
PATCHES = {
    'synth_fl/utils/__init__.py': ('path_manager = PathManager()\n',
        'path_manager = PathManager()\nDEFAULT_DATA_ROOT = path_manager.DEFAULT_DATA_ROOT\nWANDB_PROJECT_NAME = path_manager.WANDB_PROJECT_NAME\n'),
    'synth_fl/utils/dataloaders/core.py': ('from synth_fl.utils import logger\n',
        'from synth_fl.utils import logger, path_manager\n'),
    'synth_fl/generators/central/__init__.py': ('from .ctgan import CTGAN\n',
        '# CTGAN import disabled for the non-neural FLAIM reference; upstream\n# FederatedDLConfig is absent in this pinned source.\n'),
    'synth_fl/generators/federated/__init__.py': ('from synth_fl.generators.federated.fed_ctgan import FedCTGAN\n',
        '# FedCTGAN import disabled for the non-neural FLAIM reference; upstream\n# FederatedDLConfig is absent in this pinned source.\n'),
}

def main() -> None:
    out = []
    for name, (old, new) in PATCHES.items():
        path = ROOT / name
        before = path.read_bytes()
        content = before.decode()
        if new not in content:
            if content.count(old) != 1:
                raise ValueError(f'Unexpected upstream content: {name}')
            path.write_text(content.replace(old, new))
        if name == 'synth_fl/generators/central/__init__.py':
            content = path.read_text()
            old_map = '    "ctgan": CTGAN,\n'
            if old_map in content:
                path.write_text(content.replace(old_map, ''))
        if name == 'synth_fl/generators/federated/__init__.py':
            content = path.read_text()
            old_map = '    "fedctgan": FedCTGAN,\n'
            if old_map in content:
                path.write_text(content.replace(old_map, ''))
        out.append({'path': name, 'sha256_before': hashlib.sha256(before).hexdigest(),
                    'sha256_after': hashlib.sha256(path.read_bytes()).hexdigest()})
    Path('/home/ubuntu/research-director/btp-federated-statistics-20261024/btp_ec2_handoff/reports/published_references/flaim_import_patch.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out))

if __name__ == '__main__':
    main()
