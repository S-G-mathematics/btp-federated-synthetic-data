"""Package only current-source validated smoke evidence and project deliverables."""
import argparse,hashlib,json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dest',default='../output/handoff');args=ap.parse_args()
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from btp.run import code_hash
    dest=(root/args.dest).resolve();dest.mkdir(parents=True,exist_ok=True)
    current=code_hash();cells=[]
    for path in sorted((root/'results/final_validated_smoke').glob('*/STATUS.json')):
        config=json.loads((path.parent/'configuration.json').read_text());status=json.loads(path.read_text())
        if config['code_hash']!=current:continue
        stages=sorted(int(p.name[3:5]) for p in path.parent.glob('exp*_complete.json'))
        if stages!=list(range(1,13)):raise RuntimeError('Incomplete smoke cell '+str(path))
        if config['reference_role']!='development_assessment':raise RuntimeError('Official test used in handoff smoke')
        fits=json.loads((path.parent/'weight_fits.json').read_text())
        cells.append({'generator':config['generator'],'experiments':stages,'reference_role':config['reference_role'],
            'candidate_successes':[r['method'] for r in fits['methods'] if r['success']],
            'candidate_failures':[r['method'] for r in fits['methods'] if not r['success']],
            'evidence_directory':str(path.parent.relative_to(root)),
            'elapsed_seconds':status['elapsed_seconds'],'scope':'mechanical smoke, 1500 training rows total, 5 clients, 500 synthetic rows'})
    if len(cells)!=4:raise RuntimeError(f'Need 4 current-source smoke cells, found {len(cells)}')
    testlog=(root/'logs/local_tests.log').read_text();match=re.search(r'(\d+) passed',testlog)
    if not match or 'FAILED' in testlog:raise RuntimeError('Tests not fully passed')
    ntests=int(match.group(1));data=json.loads((root/'data/data_manifest.json').read_text())
    validation={'validated_utc':datetime.now(timezone.utc).isoformat(),'tests_passed':ntests,
        'dataset_rows':data['source_rows'],'smoke_cells':cells,'code_hash':current,
        'scientific_full_data_study_completed':False,'ec2_execution_performed_in_this_session':False,
        'primary_distance':'empirical real D_R versus generated D_S',
        'official_test_scored_in_smoke':False}
    (root/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
    (root/'STATUS.md').write_text(f'''# Verified handoff status

- Official UCI Adult downloaded/audited: 48,842 source records, 14 predictors + binary income.
- 25 training rows matching official-test records quarantined; grouped development splits.
- {ntests} correctness/leakage/solver/model/privacy tests passed.
- Four non-neural generators each executed all twelve small smoke stages (48 stage markers).
- All smoke runs used development-assessment rows; official test was not scored.
- Eight literature-inspired candidate families plus auxiliary baselines are implemented; exactness and access differences are explicit.
- Actual checkpoints, synthetic datasets, CSV/JSON metrics, logs and a reproducible figure are included.
- Smoke runs validate software, not scientific ranking, novelty, full-data accuracy or publishability.
- No EC2 execution from this preparation chat; next is remote verification and full-data Exp 1/2.
- Scientific completion/extension requirements: docs/EXPERIMENTS_12.md.

See VALIDATION.json, logs/local_tests.log, and results/final_validated_smoke/.
''')
    with (root/'logs/local_dependencies.freeze.txt').open('w') as out:
        subprocess.run([sys.executable,'-m','pip','freeze'],stdout=out,check=True)
    def include(p):
        rel=p.relative_to(root)
        if not p.is_file() or any(x in {'.git','.venv','__pycache__','.pytest_cache'} for x in rel.parts):return False
        if p.suffix=='.pyc' or p.name=='SHA256SUMS.json':return False
        if rel.parts[0]=='results':return len(rel.parts)>1 and rel.parts[1]=='final_validated_smoke'
        if rel.parts[0]=='logs':return p.name in {'local_tests.log','data_validation.log','local_dependencies.freeze.txt'} or p.name.endswith('_final_smoke.log')
        if len(rel.parts)==1 and p.suffix=='.log':return False
        return True
    files=sorted(p for p in root.rglob('*') if include(p))
    sums={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (root/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2,sort_keys=True)+'\n')
    archive=dest/'BTP_EC2_Complete_Handoff_20261024.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[root/'SHA256SUMS.json']:
            z.write(p,arcname=str(Path('btp_ec2_handoff')/p.relative_to(root)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,sha in sums.items():
            assert hashlib.sha256(z.read('btp_ec2_handoff/'+name)).hexdigest()==sha
    prompt=dest/'BTP_START_ON_EC2.txt';shutil.copy2(root/'BTP_START_ON_EC2.txt',prompt)
    print(json.dumps({'zip':str(archive),'zip_bytes':archive.stat().st_size,'files':len(files)+1,
        'prompt':str(prompt),'tests_passed':ntests,'smoke_cells':len(cells),'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
