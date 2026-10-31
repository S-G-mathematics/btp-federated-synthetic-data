"""Postpilot F4/F6 variant: minimax query error under an L1 client-mass budget.

Only released pilot query means and target calibration means enter the solver.
Real validation and assessment rows stay in this privileged evaluator.
"""
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, pickle, platform, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linprog
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from btp.data import prepare_splits, ALL_COLUMNS
from btp.privacy import public_schema
from btp.evaluation import public_workloads, empirical_metrics, sample_mixture


def solve_budget_minimax(H,b,alpha,budget):
    H=np.asarray(H,float);b=np.asarray(b,float);alpha=np.asarray(alpha,float)
    L,K=H.shape
    if b.shape!=(L,) or alpha.shape!=(K,) or not 0<=budget<=2:
        raise ValueError('invalid summary shape or L1 budget')
    c=np.zeros(2*K+1);c[-1]=1
    zero=np.zeros((L,K));ones=np.ones((L,1))
    row_pos=np.c_[H,zero,-ones];row_neg=np.c_[-H,zero,-ones]
    ident=np.eye(K);z=np.zeros((K,1))
    # w-alpha <= u and alpha-w <= u, with sum(u) <= budget.
    dev_pos=np.c_[ident,-ident,z];dev_neg=np.c_[-ident,-ident,z]
    budget_row=np.r_[np.zeros(K),np.ones(K),0.][None,:]
    Aub=np.vstack([row_pos,row_neg,dev_pos,dev_neg,budget_row])
    bub=np.r_[b,-b,alpha,-alpha,budget]
    eq=np.r_[np.ones(K),np.zeros(K+1)][None,:]
    res=linprog(c,A_ub=Aub,b_ub=bub,A_eq=eq,b_eq=[1.],
                bounds=[(0,1)]*K+[(0,None)]*K+[(0,None)],method='highs')
    if not res.success:raise RuntimeError(f'budget LP failed: {res.message}')
    w=res.x[:K]
    if abs(w.sum()-1)>1e-7 or np.min(w)<-1e-8 or np.abs(w-alpha).sum()>budget+1e-7:
        raise RuntimeError('budget LP returned invalid weights')
    return w,{'solver':'HiGHS','status':int(res.status),'message':res.message,
              'objective_calibration_query_linf':float(np.max(np.abs(H@w-b))),
              'simplex_valid':True,'actual_weight_l1':float(np.abs(w-alpha).sum())}


def self_test():
    H=np.eye(2);b=np.array([.9,.1]);a=np.array([.5,.5])
    w0,_=solve_budget_minimax(H,b,a,0)
    w1,_=solve_budget_minimax(H,b,a,.4)
    w2,_=solve_budget_minimax(H,b,a,2)
    np.testing.assert_allclose(w0,[.5,.5],atol=1e-8)
    np.testing.assert_allclose(w1,[.7,.3],atol=1e-8)
    np.testing.assert_allclose(w2,[.9,.1],atol=1e-8)


def main():
    self_test()
    ap=argparse.ArgumentParser()
    ap.add_argument('--cell',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--rows',type=int,default=10000)
    ap.add_argument('--repeats',type=int,default=3)
    a=ap.parse_args();start=time.monotonic();a.out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((a.cell/'configuration.json').read_text())
    if cfg['reference_role']!='development_assessment':raise ValueError('official test blocked')
    resources=yaml.safe_load((ROOT/'configs/resources.yaml').read_text())
    lane=Path(os.path.expanduser(resources['shared_compute_lease']));lane.parent.mkdir(parents=True,exist_ok=True)
    lease=lane.open('a+')
    try:fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Shared heavy-compute lease occupied')
    mem=Path('/proc/meminfo').read_text();avail=next(int(line.split()[1])*1024 for line in mem.splitlines() if line.startswith('MemAvailable:'))
    if avail<resources['minimum_available_ram_gib']*2**30 or shutil.disk_usage(ROOT).free<resources['minimum_free_disk_gib']*2**30:
        raise RuntimeError('resource reserve reached')
    summary=np.load(a.cell/'releases/permitted_summary.npz')
    H=summary['H'];b=summary['target_query_mean'];alpha=summary['alpha']
    manifest_path=a.cell/'partition_manifest.csv'
    manifest=pd.read_csv(manifest_path,dtype={'row_id':str})
    splits=prepare_splits(ROOT/'data/raw',cfg['seed'])
    dev=pd.concat([splits[k] for k in ('train','tune','calibration','validation')])
    if not manifest.row_id.isin(dev.index).all():raise ValueError('split manifest mismatch')
    joined=manifest.join(dev,on='row_id',validate='one_to_one')
    parts={name:[joined[(joined.split==name)&(joined.client==i)][list(ALL_COLUMNS)].copy()
                 for i in range(cfg['k'])] for name in ('validation','test')}
    models=[pickle.loads((a.cell/'releases'/f'client_{i}.pkl').read_bytes()) for i in range(cfg['k'])]
    workload,audit=public_workloads(public_schema())
    budgets=[0.,.25,.5,.75,1.,2.]
    w_zero,_=solve_budget_minimax(H,b,alpha,0.)
    np.testing.assert_allclose(w_zero,alpha,atol=1e-7)
    w_full,cert_full=solve_budget_minimax(H,b,alpha,2.)
    existing=json.loads((a.cell/'weight_fits.json').read_text())['methods']
    original=next(x for x in existing if x['method']=='query_minimax')
    if not original['success']:
        raise RuntimeError('original query-minimax fit failed; cannot validate delta=2 endpoint')
    original_residual=float(np.max(np.abs(H@np.asarray(original['weights'])-b)))
    if abs(cert_full['objective_calibration_query_linf']-original_residual)>1e-6:
        raise RuntimeError('delta=2 LP does not match original query-minimax objective')
    records=[];fits=[]
    for delta in budgets:
        w,certificate=solve_budget_minimax(H,b,alpha,delta)
        method=f'target_budget_minimax_l1_{delta:g}'
        fits.append({'method':method,'budget':delta,'weights':w.tolist(),**certificate,
                     'effective_client_count':float(1/np.sum(w*w)),
                     'zero_weight_clients':int(np.sum(w<1e-8))})
        for split in ('validation','test'):
            reps=[0] if split=='validation' else range(a.repeats)
            for rep in reps:
                seed=cfg['seed']+(4200 if split=='validation' else 5200)+rep
                syn,counts=sample_mixture(models,w,a.rows,seed)
                metric=empirical_metrics(parts[split],syn,workload,audit,alpha)
                records.append({'method':method,'budget':delta,'split':'development_validation' if split=='validation' else 'development_assessment',
                                'replicate':rep,'weight_l1_from_alpha':certificate['actual_weight_l1'],
                                'synthetic_count_exact':int(counts.sum()==a.rows),**metric})
    df=pd.DataFrame(records)
    val=df[df.split=='development_validation']
    chosen=val.sort_values(['query_linf','unseen_query_mae','budget']).iloc[0]
    spec={'reference_cell':str(a.cell),'reference_role':cfg['reference_role'],
          'generator':cfg['generator'],'partition':cfg['partition'],'k':cfg['k'],'seed':cfg['seed'],
          'budget_grid':budgets,'selected_budget_on_validation':float(chosen.budget),
          'selection_metric':'validation query_linf then unseen_query_mae',
          'official_test_used':False,'assessment_not_used_for_selection':True,
          'rows':a.rows,'repeats':a.repeats,'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'host':platform.node(),'ended_utc':datetime.now(timezone.utc).isoformat(),
          'wall_seconds':time.monotonic()-start,'status':'completed'}
    df.to_csv(a.out/'metrics.csv',index=False)
    (a.out/'weight_fits.json').write_text(json.dumps(fits,indent=2)+'\n')
    (a.out/'configuration.json').write_text(json.dumps(spec,indent=2)+'\n')
    print(f"{a.cell.name}: selected delta={chosen.budget:g} on validation, assessment mean="
          f"{df[(df.split=='development_assessment')&(df.budget==chosen.budget)].query_linf.mean():.6f}")

if __name__=='__main__':main()
