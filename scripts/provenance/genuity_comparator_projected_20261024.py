"""Client-private sample-only comparison using the published Genuity wheel.

The fitted library objects are never serialized or released: its KDE objects
retain training values, so this is outside the BTP model-release protocol.
"""
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, platform, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from btp.data import prepare_splits, NUMERIC, CATEGORICAL, ALL_COLUMNS
from btp.privacy import public_schema
from btp.evaluation import public_workloads, empirical_metrics, column_metrics


def utc():return datetime.now(timezone.utc).isoformat()

def allocation(alpha,n):
    exact=n*alpha;counts=np.floor(exact).astype(int)
    counts[np.argsort(-(exact-counts),kind='stable')[:n-counts.sum()]]+=1
    assert counts.sum()==n and np.all(np.abs(counts-exact)<1)
    return counts


def support_diagnostics(frame,schema):
    issues=np.zeros(len(frame),dtype=bool);noninteger=np.zeros(len(frame),dtype=bool)
    for c in NUMERIC:
        x=pd.to_numeric(frame[c],errors='coerce').to_numpy(float)
        lo,hi=schema['numeric_ranges'][c]
        issues|=~np.isfinite(x)|(x<lo)|(x>hi)
        noninteger|=~np.isfinite(x)|(np.abs(x-np.rint(x))>1e-9)
    for c,cats in schema['categories'].items():issues|=~frame[c].astype(str).isin(cats).to_numpy()
    return {'invalid_public_support_row_fraction':float(issues.mean()),
            'noninteger_numeric_row_fraction':float(noninteger.mean()),
            'invalid_income_row_fraction':float((~frame.income.isin(['<=50K','>50K'])).mean())}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference-cell',type=Path,required=True)
    ap.add_argument('--method',choices=['kde','copula'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--rows',type=int,default=10000)
    ap.add_argument('--repeats',type=int,default=1)
    ap.add_argument('--train-cap',type=int,default=0)
    ap.add_argument('--project-integers',action='store_true')
    a=ap.parse_args();begin=time.monotonic();a.out.mkdir(parents=True,exist_ok=True)
    if a.rows<1 or a.repeats<1 or a.train_cap<0:raise ValueError('invalid budget')
    cell=a.reference_cell
    cfg=json.loads((cell/'configuration.json').read_text())
    if cfg['reference_role']!='development_assessment':raise ValueError('official test blocked for comparator')
    partition=json.loads((cell/'partition.json').read_text())
    alpha=np.asarray(partition['alpha'],float)
    manifest_path=cell/'partition_manifest.csv'
    manifest=pd.read_csv(manifest_path,dtype={'row_id':str})
    splits=prepare_splits(ROOT/'data/raw',seed=cfg['seed'])
    dev=pd.concat([splits[k] for k in ('train','tune','calibration','validation')])
    if not manifest.row_id.isin(dev.index).all() or manifest.row_id.duplicated().any():
        raise ValueError('manifest mismatch')
    joined=manifest.join(dev,on='row_id',validate='one_to_one')
    parts={split:[joined[(joined.split==split)&(joined.client==i)][list(ALL_COLUMNS)].copy()
                  for i in range(cfg['k'])] for split in ('train','validation','test')}
    if any(len(f)<10 for f in parts['train']):raise ValueError('tiny client')
    import genuity
    if not genuity.check_activation():raise RuntimeError('published Genuity wheel has no active signed license')
    from importlib.metadata import version
    if version('genuity')!='2.0.2':raise RuntimeError('unexpected Genuity package version')
    from genuity.tabular.generators.kde import KDEGenerator
    from genuity.tabular.generators.copula import CopulaGenerator
    schema=public_schema();workload,audit=public_workloads(schema)
    counts=allocation(alpha,a.rows)
    spec={'method':a.method,'rows':a.rows,'repeats':a.repeats,'train_cap':a.train_cap,
          'numeric_projection':'declared_public_integer_rounding' if a.project_integers else 'none',
          'reference_cell':str(cell),'reference_role':cfg['reference_role'],
          'partition':cfg['partition'],'clients':cfg['k'],'seed':cfg['seed'],
          'target_alpha':alpha.tolist(),'synthetic_client_counts':counts.tolist(),
          'genuity_version':version('genuity'),'genuity_package_source':'published PyPI wheel',
          'model_release':'none; fit objects stay client-private in this simulated process',
          'comparison_access':'sample-only client-private model, no privileged real calibration scores',
          'training_rows_source':'client train only; no tune/calibration/validation/test fit',
          'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'host':platform.node(),'started_utc':utc()}
    (a.out/'configuration.json').write_text(json.dumps(spec,indent=2)+'\n')
    import yaml
    resources=yaml.safe_load((ROOT/'configs/resources.yaml').read_text())
    lane=Path(os.path.expanduser(resources['shared_compute_lease']))
    lane.parent.mkdir(parents=True,exist_ok=True)
    lease=lane.open('a+')
    try:fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Shared heavy-compute lease occupied')
    memory=Path('/proc/meminfo').read_text()
    available=next(int(line.split()[1])*1024 for line in memory.splitlines() if line.startswith('MemAvailable:'))
    if available<resources['minimum_available_ram_gib']*2**30:raise RuntimeError('Insufficient available RAM')
    if shutil.disk_usage(ROOT).free<resources['minimum_free_disk_gib']*2**30:raise RuntimeError('Disk reserve reached')
    models=[];timings=[]
    for i,frame in enumerate(parts['train']):
        if a.train_cap and len(frame)>a.train_cap:
            frame=frame.sample(a.train_cap,random_state=cfg['seed']+i).sort_index()
        kwargs={'random_seed':cfg['seed']+31*i,'verbose':False}
        model=(KDEGenerator(bandwidth='scott',copula_type='none',**kwargs)
               if a.method=='kde' else CopulaGenerator(copula_type='gaussian',**kwargs))
        start=time.monotonic()
        model.fit(frame,categorical_cols=list(CATEGORICAL)+['income'],continuous_cols=list(NUMERIC))
        timings.append({'client':i,'train_rows':len(frame),'fit_seconds':time.monotonic()-start})
        models.append(model)
    rows=[]
    for rep in range(a.repeats):
        samples=[]
        for i,(model,n) in enumerate(zip(models,counts)):
            if a.method=='copula':
                # Published v2 generate(seed=...) ignores seed; core uses this
                # private state to produce distinct, documented draws.
                model._core.random_seed=cfg['seed']+1009*(i+1)+rep
            start=time.monotonic()
            result=model.generate(int(n),seed=cfg['seed']+1009*(i+1)+rep)
            frame=result.data
            if len(frame)!=n or set(frame.columns)!=set(ALL_COLUMNS):
                raise RuntimeError(f'client {i} sample count/schema mismatch')
            samples.append(frame[list(ALL_COLUMNS)])
            timings.append({'client':i,'replicate':rep,'sample_rows':int(n),
                            'sample_seconds':time.monotonic()-start})
        ds=pd.concat(samples,ignore_index=True).sample(frac=1,random_state=cfg['seed']+rep).reset_index(drop=True)
        preprojection=support_diagnostics(ds,schema)
        if a.project_integers:
            for c in NUMERIC:
                x=pd.to_numeric(ds[c],errors='coerce').to_numpy(float)
                if not np.isfinite(x).all():raise RuntimeError('nonfinite numeric value before projection')
                ds[c]=np.rint(x).astype(np.int64)
        support=support_diagnostics(ds,schema)
        support['preprojection_noninteger_numeric_row_fraction']=preprojection['noninteger_numeric_row_fraction']
        support['preprojection_invalid_public_support_row_fraction']=preprojection['invalid_public_support_row_fraction']
        support['numeric_projection']=spec['numeric_projection']
        if support['invalid_income_row_fraction']>0:
            raise RuntimeError('Genuity emitted invalid income label; no successful metric row')
        for split in ('validation','test'):
            metric=empirical_metrics(parts[split],ds,workload,audit,alpha)
            rows.append({'method':'genuity_'+a.method+('_projected' if a.project_integers else '')+'_size','replicate':rep,
                         'reference_role':'development_validation' if split=='validation' else 'development_assessment',
                         **metric,**support})
        if rep==0:
            pd.DataFrame(column_metrics(parts['test'],ds,alpha,schema['numeric_ranges'])).to_csv(a.out/'columns_assessment.csv',index=False)
            ds.to_csv(a.out/'synthetic_rep0.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(rows).to_csv(a.out/'metrics.csv',index=False)
    pd.DataFrame(timings).to_csv(a.out/'timings.csv',index=False)
    spec['ended_utc']=utc();spec['wall_seconds']=time.monotonic()-begin
    spec['status']='completed';spec['repetitions_are_synthetic_only']=True
    (a.out/'configuration.json').write_text(json.dumps(spec,indent=2)+'\n')
    print(f"genuity_{a.method} completed: {a.repeats} synthetic repeats, m={a.rows}, assessment query_linf mean="
          f"{pd.DataFrame(rows).query('reference_role == \"development_assessment\"').query_linf.mean():.6f}")

if __name__=='__main__':main()
