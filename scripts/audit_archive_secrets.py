"""Conservative private-token pattern audit; report paths/counts, never values."""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'ARTIFACT_SHA256_MANIFEST.json').read_text())
patterns={
 'aws_access_key':re.compile(rb'AKIA[0-9A-Z]{16}'),
 'private_key_pem':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'openai_style_key':re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}'),
 'jwt_like_token':re.compile(rb'eyJ[A-Za-z0-9_-]{24,}\.eyJ[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{20,}'),
}
hits=[]
for entry in manifest['files']:
    p=ROOT/entry['path']
    if p.stat().st_size>5_000_000:continue
    if p.suffix.lower() in {'.pkl','.pickle','.npz','.npy','.png','.jpg','.jpeg','.pdf','.zip','.gz','.parquet','.sqlite','.db','.woff','.ttf'}:continue
    data=p.read_bytes()
    for name,rx in patterns.items():
        count=len(rx.findall(data))
        if count:hits.append({'path':entry['path'],'pattern':name,'count':count})
print(json.dumps({'scanned_files':len(manifest['files']),'hits':hits},sort_keys=True))
if hits:raise SystemExit(1)
