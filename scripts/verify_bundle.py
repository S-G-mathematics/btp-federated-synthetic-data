"""Verify every included file against SHA256SUMS.json before executing code."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=root/'SHA256SUMS.json'
if not manifest.exists():raise SystemExit('SHA256SUMS.json absent: bundle has not been finalized')
bad=[]
for name,expected in json.loads(manifest.read_text()).items():
 p=root/name
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:bad.append(name)
if bad:raise SystemExit('Integrity mismatch: '+', '.join(bad))
print('PASS:',len(json.loads(manifest.read_text())),'bundled file hashes verified')
