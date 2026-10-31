"""Run and record only lightweight packaging-time verification commands."""
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs/packaging"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(name: str, args: list[str]) -> dict:
    start = now()
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    process = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, check=False)
    end = now()
    (LOGS / f"{name}.log").write_text(process.stdout, encoding="utf-8")
    return {"name": name, "command": args, "started_at_utc": start, "ended_at_utc": end,
            "exit_status": process.returncode, "log": f"logs/packaging/{name}.log",
            "test_result": (re.search(r"\d+ passed(?:, \d+ skipped)? in [^\n]+", process.stdout) or [None])[0]}


def main() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    versions = {name: importlib.metadata.version(name) for name in
                ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "PyYAML", "pytest")}
    environment = {"audited_at_utc": now(), "python": sys.version, "executable": sys.executable,
                   "os": platform.platform(), "architecture": platform.machine(),
                   "cpu_count": os.cpu_count(), "dependency_versions": versions,
                   "native_thread_limit": 1, "source_git_commit": None,
                   "source_git_status": "source project was not a Git repository"}
    (ROOT / "provenance/software_versions.json").write_text(json.dumps(environment, indent=2) + "\n")
    jobs = [
        ("data_sources", [sys.executable, "scripts/verify_data_sources.py"]),
        ("saved_reports", [sys.executable, "scripts/reproduce_repository.py", "--tables"]),
        ("repository_audit", [sys.executable, "scripts/audit_repository.py"]),
        ("scientific_tests", [sys.executable, "-m", "pytest", "-q"]),
    ]
    report = {"environment": "provenance/software_versions.json", "commands": [run(name, args) for name, args in jobs]}
    (LOGS / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"exit_statuses": {x["name"]: x["exit_status"] for x in report["commands"]},
                      "test_result": report["commands"][-1]["test_result"]}, indent=2))
    if any(x["exit_status"] for x in report["commands"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
