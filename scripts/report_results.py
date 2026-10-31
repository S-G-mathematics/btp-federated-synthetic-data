"""Aggregate raw result tables and draw evidence-only figures."""
import argparse,json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='results');p.add_argument('--out',default='reports');a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 tables={}
 for path in sorted(Path(a.root).rglob('exp*.csv')):
  config=path.parent/'configuration.json'
  if not config.exists():continue
  meta=json.loads(config.read_text());table=pd.read_csv(path)
  for k in ['generator','partition','k','seed','profile_name']:table[k]=meta[k]
  table['source_file']=str(path);tables.setdefault(path.name,[]).append(table)
 for name,parts in tables.items():pd.concat(parts,ignore_index=True).to_csv(out/name,index=False)
 if 'exp01_test.csv' in tables:
  frame=pd.concat(tables['exp01_test.csv'],ignore_index=True)
  by_seed=frame.groupby(['generator','method','seed'],as_index=False)['query_linf'].mean()
  by_seed.to_csv(out/'exp01_seed_level.csv',index=False)
  summary=by_seed.groupby(['generator','method'])['query_linf'].agg(['mean','std','count']).reset_index()
  summary.to_csv(out/'exp01_summary.csv',index=False)
  fig,ax=plt.subplots(figsize=(10,5))
  for generator,part in summary.groupby('generator'):
   ax.plot(part['method'],part['mean'],'o-',label=generator)
  ax.set_ylabel('Max absolute query error\n(real D_R versus synthetic D_S)')
  ax.set_xlabel('Candidate method');ax.tick_params(axis='x',rotation=65);ax.legend()
  ax.set_title('Measured runs only; smoke results are software checks')
  fig.tight_layout();fig.savefig(out/'exp01_query_fidelity.png',dpi=180);plt.close(fig)
 text=['BTP RESULTS STATUS','',f'Found {sum(map(len,tables.values()))} result tables.','',
       'This report contains only executed records. Smoke profiles are not publication evidence.',
       'Choose/freeze methods from development validation results; do not rank/select using final test.',
       'Independent seeds, paired comparisons, uncertainty intervals and baseline fidelity must be audited before a paper claim.']
 (out/'STATUS.txt').write_text('\n'.join(text)+'\n')
 print('Wrote',out)

if __name__=='__main__':main()
