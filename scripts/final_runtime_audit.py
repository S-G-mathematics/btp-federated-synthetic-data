"""Summarize recorded completion runtime without inferring cloud cost."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
state = json.loads((ROOT / "COMPLETION_STATE.json").read_text(encoding="utf-8"))
cells = list((ROOT / "results/adult_confirmation_20261025").glob("*/complete.json"))
if len(cells) != 12:
    raise SystemExit(f"expected twelve confirmation primary cells, got {len(cells)}")
primary = sum(float(json.loads(p.read_text()).get("elapsed_seconds", 0.0)) for p in cells)
logs = {}
for name in ("adult_confirmation_primary_20261025.log", "adult_confirmation_secondary_20261025.log"):
    p = ROOT / "logs" / name
    st = p.stat()
    logs[name] = {"bytes": st.st_size, "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(), "ctime_utc": datetime.fromtimestamp(st.st_ctime, timezone.utc).isoformat()}
first = json.loads((ROOT / "reports/confirmation/FIRST_OFFICIAL_TEST_READ.json").read_text())
start = datetime.fromisoformat(first["first_access_at_utc"])
end = datetime.fromtimestamp((ROOT / "logs/adult_confirmation_secondary_20261025.log").stat().st_mtime, timezone.utc)
confirmation_invocation_upper = max((end-start).total_seconds(),primary)
prior_upper = float(state["incremental_worker_seconds_used"])
# Prior register upper bounds include failed attempts; full confirmation interval includes
# idle/reporting time and thus conservatively bounds both confirmation invocations.
total_upper = prior_upper + confirmation_invocation_upper
report = {"created_at_utc":datetime.now(timezone.utc).isoformat(),
          "primary_sum_marker_elapsed_seconds":primary,
          "confirmation_upper_seconds_first_test_read_to_secondary_log_mtime":confirmation_invocation_upper,
          "pre_confirmation_registered_upper_seconds":prior_upper,
          "incremental_worker_upper_seconds":total_upper,
          "incremental_worker_upper_hours":total_upper/3600,
          "cap_seconds":86400,
          "under_cap":total_upper < 86400,
          "accounting_limits":"Confirmation interval includes idle/reporting and begins at first test read, so it is conservative; earlier phase entries are rounded upper bounds from run logs. No AWS dollar/hourly rate inferred.",
          "logs":logs}
dest=ROOT/"reports/resources/completion_runtime.json"
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,sort_keys=True))
