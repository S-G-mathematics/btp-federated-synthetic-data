#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
if [ -e .venv ]; then
  echo 'A project .venv already exists; use a fresh extraction for this bootstrap.' >&2
  exit 2
fi
python3 - <<'PY'
import sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit('Use Python 3.12 for the recorded final-package environment')
print('Python:', sys.version.split()[0])
PY
python3 -m venv .venv
.venv/bin/python -m pip install -r environment/requirements_final_portable_20261025.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m pip freeze > logs/final_cleanroom_dependencies.freeze.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/freeze_gate.py --freeze SELECTION_FROZEN.json --root .
.venv/bin/python scripts/verify_final_package.py
echo 'Final-package bootstrap and saved-artifact checks passed.'
