"""Descriptive split-seed and synthetic-repeat summary; official test untouched."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'results/ec2_copula_replication_20261024'
out=ROOT/'reports/copula_replication_20261024';out.mkdir(parents=True,exist_ok=True)
rows=[]
for cell in sorted(source.iterdir()):
 if not (cell/'exp02_complete.json').exists():continue
 c=json.loads((cell/'configuration.json').read_text())
 if c['reference_role']!='development_assessment':raise ValueError('unexpected official test')
 v=pd.read_csv(cell/'exp01_validation.csv').set_index('method')
 a=pd.read_csv(cell/'exp01_test.csv')
 winner=json.loads((cell/'STATUS.json').read_text())['winner_validation']
 for method,g in a.groupby('method'):
  rows.append({'cell':cell.name,'partition':c['partition'],'k':c['k'],'split_seed':c['seed'],
               'code_hash':c['code_hash'],'method':method,
               'selected_within_cell':method==winner,'validation_query_linf':v.loc[method,'query_linf'],
               'assessment_query_linf_seed_mean':g.query_linf.mean(),
               'assessment_query_linf_synthetic_sd':g.query_linf.std(),
               'synthetic_repeats':len(g),
               'assessment_unseen_query_mae_seed_mean':g.unseen_query_mae.mean()})
x=pd.DataFrame(rows);x.to_csv(out/'cell_method_seed_means.csv',index=False)
y=x.groupby(['partition','k','method']).agg(
    split_seeds=('split_seed','nunique'),
    assessment_query_linf_mean_over_seeds=('assessment_query_linf_seed_mean','mean'),
    assessment_query_linf_sd_over_seeds=('assessment_query_linf_seed_mean','std'),
    validation_query_linf_mean_over_seeds=('validation_query_linf','mean'),
    mean_synthetic_repeat_sd=('assessment_query_linf_synthetic_sd','mean')).reset_index()
y.to_csv(out/'method_split_seed_summary.csv',index=False)
policy=x[x.selected_within_cell]
size=x[x.method=='size'][['partition','k','split_seed','assessment_query_linf_seed_mean']].rename(columns={'assessment_query_linf_seed_mean':'size_assessment_seed_mean'})
policy=policy.merge(size,on=['partition','k','split_seed'],validate='one_to_one')
policy['policy_minus_size_assessment']=policy.assessment_query_linf_seed_mean-policy.size_assessment_seed_mean
policy.to_csv(out/'within_cell_validation_policy.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ax,k in zip(axes,[5,10]):
 z=y[(y.k==k)&(y.method.isin(['size','entropy_calibration','kernel_mean_matching','uncertainty_gls']))]
 for method,g in z.groupby('method'):
  g=g.set_index('partition').reindex(['age','age_education','label_skew'])
  ax.plot(['Age','Age + education','Label skew'],g.assessment_query_linf_mean_over_seeds,marker='o',label=method)
 ax.set_title(f'K={k}, seeds 202/303');ax.grid(alpha=.2)
axes[0].set_ylabel('Assessment query max error, mean of split-seed means')
axes[1].legend(fontsize=7)
fig.suptitle('Copula development replication; overlapping Adult rows, no independent-cohort CI')
fig.tight_layout();fig.savefig(out/'copula_method_replication.png',dpi=160)
print(f'reported {len(x)} method-seed rows from {x.cell.nunique()} cells')
