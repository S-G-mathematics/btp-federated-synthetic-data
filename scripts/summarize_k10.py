"""Descriptive K=10 seed101 trade-off from corrected development cells."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1]
x=pd.read_csv(r/'reports/development_k10_stacking_fixed_20261024/method_audit.csv')
out=r/'reports/k10_seed101_diagnostics';out.mkdir(parents=True,exist_ok=True)
x.to_csv(out/'candidate_methods.csv',index=False)
sel=x[x.selected_within_cell & x.fit_success]
size=x[x.method.eq('size')][['cell','assessment_query_linf_mean']].rename(columns={'assessment_query_linf_mean':'size_assessment_query_linf_mean'})
s=sel.merge(size,on='cell',validate='one_to_one')
s['assessment_difference_vs_size']=s.assessment_query_linf_mean-s.size_assessment_query_linf_mean
s.to_csv(out/'within_cell_validation_selection.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(14,4),sharey=True)
for ax,part in zip(axes,['age','age_education','label_skew']):
 g=x[(x.partition==part)&x.fit_success]
 ax.scatter(g.weight_l1_from_target_alpha,g.validation_query_linf,s=20,alpha=.32,c='#61758a')
 t=g[g.selected_within_cell]
 ax.scatter(t.weight_l1_from_target_alpha,t.validation_query_linf,s=58,c='#c44e52',label='within-cell validation choice')
 ax.set_title(part.replace('_',' + '));ax.set_xlabel('L1 weight distance from fixed target alpha');ax.grid(alpha=.2)
axes[0].set_ylabel('Validation query max error');axes[0].legend(loc='upper left',fontsize=7)
fig.suptitle('K=10 seed 101: fidelity and client representation (development only)')
fig.tight_layout();fig.savefig(out/'validation_fidelity_vs_representation.png',dpi=160)
print('saved K10 candidate and selection diagnostics')
