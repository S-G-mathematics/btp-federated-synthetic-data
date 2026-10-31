#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results logs
python3 - <<'PY'
import platform,sys,shutil
from pathlib import Path
print('Host:',platform.node(),'Python:',sys.version)
if sys.version_info < (3,11):
 raise SystemExit('Need Python >=3.11. Create an isolated suitable environment; do not modify system Python.')
print('Disk available GiB:',round(shutil.disk_usage('.').free/2**30,2))
print('Workspace:',Path.cwd())
PY
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install 'setuptools>=68' wheel
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pip freeze > logs/ec2_dependencies.freeze.txt
.venv/bin/python scripts/verify_bundle.py
.venv/bin/python scripts/validate_data.py
.venv/bin/python -m pytest -q | tee logs/ec2_tests.log
echo 'Bootstrap complete. Start the bounded smoke command in README.md.'
