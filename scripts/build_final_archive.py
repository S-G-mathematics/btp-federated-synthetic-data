"""Create a complete hash-verified private BTP archive from the project tree."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent
OUT=PARENT/'BTP_FINAL_EXPERIMENTAL_PACKAGE_20261025_v2.zip'
ORIGINAL=PARENT/'BTP_EC2_Complete_Handoff_20261024.zip'
MANIFEST=ROOT/'ARTIFACT_SHA256_MANIFEST.json'
EXCLUDE_DIRS={'.venv','.git','.pytest_cache','__pycache__','tmp','genuity_env','private','.mypy_cache','.ruff_cache'}
EXCLUDE_NAMES={'ARTIFACT_SHA256_MANIFEST.json','.DS_Store'}
EXCLUDE_SUFFIXES={'.pyc','.pyo','.pem','.key'}

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()

def collect()->list[Path]:
    files=[]
    for base,dirs,names in os.walk(ROOT):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDE_DIRS)
        for name in sorted(names):
            p=Path(base)/name
            rel=p.relative_to(ROOT)
            if name in EXCLUDE_NAMES or p.suffix.lower() in EXCLUDE_SUFFIXES:
                continue
            if p.is_symlink():
                raise ValueError(f'symlink in package: {rel}')
            if any(x.lower() in {'credential','credentials','secret','secrets'} for x in rel.parts):
                raise ValueError(f'sensitive path in package: {rel}')
            files.append(p)
    return files

def build():
    if not ORIGINAL.exists():
        raise FileNotFoundError(ORIGINAL)
    files=collect()
    needed=['SELECTION_FROZEN.json','EXTERNAL_PROTOCOL_FROZEN.json','BTP_FINAL_EXPERIMENTAL_REPORT.md',
            'BTP_FINAL_EXPERIMENTAL_REPORT.pdf','EXPERIMENTS_01_TO_12_CLOSURE.json',
            'ALL_RUNS_INDEX.csv','reports/final_build/summary.json','logs/verify_final_package_terminal_20261025.log']
    seen={p.relative_to(ROOT).as_posix() for p in files}
    missing=set(needed)-seen
    if missing:raise ValueError(f'missing required files: {sorted(missing)}')
    entries=[]
    for p in files:
        entries.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),
              'archive_name':OUT.name,'root':'btp_ec2_handoff/',
              'hash':'SHA-256','file_count':len(entries),'files':entries,
              'original_handoff_zip':{'path':'ORIGINAL_HANDOFF/'+ORIGINAL.name,'bytes':ORIGINAL.stat().st_size,'sha256':digest(ORIGINAL)},
              'excluded':'virtual environments, caches, temporary PDF renders, credentials/keys, unrelated projects; project checkpoints and raw logs retained'}
    MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    temp=OUT.with_suffix('.zip.partial')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in files:
            z.write(p,'btp_ec2_handoff/'+p.relative_to(ROOT).as_posix())
        z.write(MANIFEST,'btp_ec2_handoff/'+MANIFEST.name)
        z.write(ORIGINAL,'ORIGINAL_HANDOFF/'+ORIGINAL.name)
    temp.replace(OUT)
    with zipfile.ZipFile(OUT) as z:
        bad=z.testzip()
        if bad:raise ValueError(f'ZIP CRC failure: {bad}')
        names=set(z.namelist())
        if len(names)!=len(files)+2:
            raise ValueError('ZIP entry count mismatch')
    result={'archive':str(OUT),'archive_bytes':OUT.stat().st_size,'archive_sha256':digest(OUT),
            'file_count':len(entries),'manifest_sha256':digest(MANIFEST),'original_zip_sha256':manifest['original_handoff_zip']['sha256']}
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':build()
