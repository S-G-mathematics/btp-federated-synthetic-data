"""Descriptive K=5 development diagnostics; never selects on assessment."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sources=[ROOT/'reports/development_audit_20261024/method_audit.csv',
         ROOT/'reports/development_skew_20261024/method_audit.csv']
x=pd.concat([pd.read_csv(p) for p in sources],ignore_index=True)
# The first source contains both original and expanded-grid age cells.
priority={'ec2_pilot_gls_fixed_20261024':0,'ec2_pilot_added_20261024':1,
          'ec2_pilot_extended_grid_20261024':2,'ec2_development_skew_20261024':3}
def rank(cell):
    if cell.startswith(('independent_age_k5_s101_48d','mixed_gmm_age_k5_s101_324')):return 2
    if cell.startswith(('latent_class_age_','prototype_kde_age_')):return 1
    return 0
x['priority']=x.cell.map(rank)
x=x.sort_values('priority').drop_duplicates(['generator','partition','clients','seed','method'],keep='last')
out=ROOT/'reports/k5_seed101_diagnostics';out.mkdir(parents=True,exist_ok=True)
x.drop(columns='priority').to_csv(out/'candidate_methods.csv',index=False)
selected=x[x.selected_within_cell & x.fit_success]
size=x[x.method.eq('size') & x.fit_success][['generator','partition','assessment_query_linf_mean']].rename(columns={'assessment_query_linf_mean':'size_assessment_query_linf_mean'})
s=selected.merge(size,on=['generator','partition'],validate='one_to_one')
s['assessment_difference_vs_size']=s.assessment_query_linf_mean-s.size_assessment_query_linf_mean
s.to_csv(out/'within_cell_validation_selection.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(14,4),sharey=True)
for ax,part in zip(axes,['age','age_education','label_skew']):
    g=x[(x.partition==part)&x.fit_success]
    ax.scatter(g.weight_l1_from_target_alpha,g.validation_query_linf,s=22,alpha=.35,c='#61758a')
    sel=g[g.selected_within_cell]
    ax.scatter(sel.weight_l1_from_target_alpha,sel.validation_query_linf,s=58,c='#c44e52',label='within-cell validation choice')
    ax.set_title(part.replace('_',' + '));ax.set_xlabel('L1 weight distance from fixed target alpha')
    ax.grid(alpha=.2)
axes[0].set_ylabel('Validation query max error')
axes[0].legend(loc='upper left',fontsize=7)
fig.suptitle('K=5 seed 101: fidelity and client representation (development only)')
fig.tight_layout();fig.savefig(out/'validation_fidelity_vs_representation.png',dpi=160)
print(f'saved {len(x)} candidate rows, {len(s)} within-cell choices')
