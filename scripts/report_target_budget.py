"""Summarize fixed-pilot target-distance ablations without selecting on assessment."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1]
roots=['target_budget_copula_label_k10_20261024','target_budget_copula_age_k10_20261024',
       'target_budget_independent_age_education_k10_20261024']
rows=[]
for name in roots:
 p=r/'results'/name;cfg=json.loads((p/'configuration.json').read_text());m=pd.read_csv(p/'metrics.csv')
 for f in json.loads((p/'weight_fits.json').read_text()):
  delta=f['budget'];v=m[(m.split=='development_validation')&(m.budget==delta)]
  a=m[(m.split=='development_assessment')&(m.budget==delta)]
  rows.append({'cell':cfg['reference_cell'].split('/')[-1],
      'generator':cfg['generator'],'partition':cfg['partition'],'k':cfg['k'],
      'declared_L1_budget':delta,'actual_L1_from_alpha':f['actual_weight_l1'],
      'effective_client_count':f['effective_client_count'],
      'zero_weight_clients':f['zero_weight_clients'],
      'validation_query_linf':v.query_linf.iloc[0],
      'assessment_query_linf_mean':a.query_linf.mean(),
      'assessment_query_linf_sd_synthetic':a.query_linf.std(),
      'synthetic_repeats':len(a),'selected_on_validation':delta==cfg['selected_budget_on_validation']})
out=r/'reports/target_budget_20261024';out.mkdir(parents=True,exist_ok=True)
x=pd.DataFrame(rows);x.to_csv(out/'budget_tradeoff.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(14,4),sharey=False)
for ax,((gen,part),g) in zip(axes,x.groupby(['generator','partition'],sort=False)):
 g=g.sort_values('declared_L1_budget')
 ax.plot(g.actual_L1_from_alpha,g.validation_query_linf,'o-',label='validation')
 ax.errorbar(g.actual_L1_from_alpha,g.assessment_query_linf_mean,yerr=g.assessment_query_linf_sd_synthetic,fmt='s--',label='assessment ? synthetic SD')
 sel=g[g.selected_on_validation]
 ax.scatter(sel.actual_L1_from_alpha,sel.validation_query_linf,s=100,facecolors='none',edgecolors='red',label='validation-selected')
 ax.set_title(gen+' / '+part.replace('_',' + '));ax.set_xlabel('Actual L1 distance from target alpha');ax.grid(alpha=.2)
axes[0].set_ylabel('Empirical query max error');axes[0].legend(fontsize=7)
fig.suptitle('K=10 seed 101: query fidelity versus representation budget')
fig.tight_layout();fig.savefig(out/'budget_tradeoff.png',dpi=160)
print('wrote target-budget table and plot')
