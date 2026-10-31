"""Plot same-partition sample-only Genuity and BTP copula size baselines."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
a=pd.read_csv(ROOT/'reports/k5_seed101_diagnostics/candidate_methods.csv')
rows=[]
for part,path in [('age','genuity_copula_projected_pilot_20261024'),
                  ('age_education','genuity_copula_projected_age_education_20261024'),
                  ('label_skew','genuity_copula_projected_label_skew_20261024')]:
    g=pd.read_csv(ROOT/'results'/path/'metrics.csv')
    g=g[g.reference_role=='development_assessment']
    rows.append({'partition':part,'generator':'Genuity projected copula','protocol':'client-private sample-only',
                 'mean_query_linf':g.query_linf.mean(),'sd_synthetic':g.query_linf.std(),'repeats':len(g),
                 'invalid_schema_fraction':g.noninteger_numeric_row_fraction.max()+g.invalid_public_support_row_fraction.max()})
    b=a[(a.generator=='copula')&(a.partition==part)&(a.method=='size')].iloc[0]
    rows.append({'partition':part,'generator':'BTP copula','protocol':'released model and size weights',
                 'mean_query_linf':b.assessment_query_linf_mean,'sd_synthetic':b.assessment_query_linf_sd_synthetic,
                 'repeats':int(b.assessment_repeats),'invalid_schema_fraction':0.})
out=ROOT/'reports/genuity_comparison_20261024';out.mkdir(parents=True,exist_ok=True)
x=pd.DataFrame(rows);x.to_csv(out/'copula_size_comparison.csv',index=False)
fig,ax=plt.subplots(figsize=(7.5,4))
for offset,gen,color in [(-.17,'BTP copula','#4c78a8'),(.17,'Genuity projected copula','#f58518')]:
    z=x[x.generator==gen].set_index('partition').loc[['age','age_education','label_skew']]
    coords=[i+offset for i in range(3)]
    ax.bar(coords,z.mean_query_linf,width=.32,yerr=z.sd_synthetic,color=color,label=gen,capsize=3)
ax.set_xticks(range(3),['Age','Age + education','Label skew'])
ax.set_ylabel('Assessment query max error')
ax.set_title('K=5 seed 101, size weights, 10,000 synthetic rows')
ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(out/'copula_size_comparison.png',dpi=160)
print('wrote Genuity comparison table and figure')
