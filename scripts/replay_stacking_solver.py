"""Reproduce stacking failures without saving privileged row-score matrices."""
from __future__ import annotations
import argparse, fcntl, json, os, pickle, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import minimize
from scipy.special import logsumexp
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from btp.data import prepare_splits, ALL_COLUMNS
from btp.run import row_likelihood


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 resources=yaml.safe_load((ROOT/'configs/resources.yaml').read_text());lane=Path(os.path.expanduser(resources['shared_compute_lease']));lane.parent.mkdir(parents=True,exist_ok=True)
 lease=lane.open('a+')
 try:fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('shared heavy-compute lease occupied')
 cfg=json.loads((a.cell/'configuration.json').read_text());alpha=np.asarray(json.loads((a.cell/'partition.json').read_text())['alpha'])
 manifest=pd.read_csv(a.cell/'partition_manifest.csv',dtype={'row_id':str})
 splits=prepare_splits(ROOT/'data/raw',cfg['seed']);dev=pd.concat([splits[k] for k in ('train','tune','calibration','validation')]);joined=manifest.join(dev,on='row_id',validate='one_to_one')
 parts=[joined[(joined.split=='calibration')&(joined.client==i)][list(ALL_COLUMNS)] for i in range(cfg['k'])]
 models=[pickle.loads((a.cell/'releases'/f'client_{i}.pkl').read_bytes()) for i in range(cfg['k'])]
 ll,floor=row_likelihood(models,pd.concat(parts));n=len(ll);sw=n*np.concatenate([np.full(len(p),v/len(p)) for p,v in zip(parts,alpha)])
 H=np.zeros((1,cfg['k']));b=np.zeros(1)
 def old_objective(w):
  return -float(sw @ logsumexp(ll+np.log(np.maximum(w,1e-300))[None,:],axis=1))
 old_res=minimize(old_objective,alpha,method='SLSQP',bounds=[(0,1)]*len(alpha),
                  constraints=[{'type':'eq','fun':lambda w:w.sum()-1}],
                  options={'maxiter':1000,'ftol':1e-10})
 def objective(w):
  denom=logsumexp(ll+np.log(np.maximum(w,1e-12))[None,:],axis=1)
  val=-float(sw@denom/n)
  gradient=-(sw@np.exp(ll-denom[:,None]))/n
  return val,gradient
 def gap(w):
  den=logsumexp(ll+np.log(np.maximum(w,1e-12))[None,:],axis=1)
  derivative=(sw@np.exp(ll-den[:,None]))/n
  return float(derivative.max()-np.dot(w,derivative))
 start=time.monotonic()
 res=minimize(objective,alpha,jac=True,method='SLSQP',bounds=[(1e-12,1.)]*len(alpha),
              constraints=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones_like(w)}],
              options={'maxiter':3000,'ftol':1e-12})
 analytic={'success':bool(res.success),'message':str(res.message),'iterations':int(res.nit),
           'mean_negative_log_score':float(objective(res.x)[0]),'duality_gap':gap(res.x),
           'wall_seconds':time.monotonic()-start,'weights':res.x.tolist()}
 start=time.monotonic();w=np.maximum(alpha,1e-12);w/=w.sum();score=objective(w)[0];iterations=0
 for iteration in range(1,10001):
  den=logsumexp(ll+np.log(w)[None,:],axis=1)
  resp=np.exp(ll+np.log(w)[None,:]-den[:,None])
  new=(sw@resp)/n;new=np.maximum(new,1e-15);new/=new.sum()
  newscore=objective(new)[0]
  w=new;iterations=iteration
  if gap(w)<1e-7:break
 em={'iterations':iterations,'mean_negative_log_score':float(objective(w)[0]),
     'duality_gap':gap(w),'wall_seconds':time.monotonic()-start,'weights':w.tolist()}
 out={'cell':a.cell.name,'rows':n,'k':len(alpha),'likelihood_floor_count':floor,
      'old_slsqp':{'success':bool(old_res.success),'message':str(old_res.message),
                   'mean_negative_log_score':float(objective(old_res.x)[0]),
                   'duality_gap':gap(old_res.x)},
      'analytic_slsqp':analytic,'em':em,
      'interpretation':'privileged evaluator reproduction; row-level likelihoods not serialized'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n')
 print(a.cell.name,'old',bool(old_res.success),'analytic',analytic['success'],'gap',round(analytic['duality_gap'],10),'em_gap',round(em['duality_gap'],10),'em_iter',iterations)

if __name__=='__main__':main()
