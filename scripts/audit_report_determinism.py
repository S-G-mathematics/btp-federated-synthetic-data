"""Require byte-identical final tables/figures on two saved-artifact rebuilds."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/final_build"


def hashes() -> dict[str, str]:
    return {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.rglob("*")) if p.is_file()}


def rebuild() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_final_reports.py"), "--build"],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    rebuild()
    first = hashes()
    rebuild()
    second = hashes()
    if not first or first != second:
        changed = sorted(set(first) ^ set(second) | {x for x in first if first.get(x) != second.get(x)})
        raise SystemExit(f"Final report rebuild is not byte deterministic: {changed}")
    print(json.dumps({"status": "byte_deterministic", "files": len(first),
                      "summary_sha256": first.get("summary.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
