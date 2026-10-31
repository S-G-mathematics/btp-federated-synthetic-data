"""Report achieved development client heterogeneity from saved row manifests."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from btp.data import prepare_splits, CATEGORICAL
from btp.privacy import public_schema


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--roots', nargs='+', type=Path, required=True)
    ap.add_argument('--raw', type=Path, default=Path('data/raw'))
    ap.add_argument('--out', type=Path, required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    schema=public_schema();cache={};rows=[];coverage=[]
    for root in a.roots:
        for cell in sorted(root.iterdir()):
            if not (cell/'exp02_complete.json').exists():continue
            cfg=json.loads((cell/'configuration.json').read_text())
            if cfg['reference_role']!='development_assessment':
                raise ValueError(f'official confirmation excluded: {cell}')
            seed=cfg['seed']
            if seed not in cache:
                splits=prepare_splits(a.raw,seed=seed)
                cache[seed]=pd.concat([splits[k] for k in ('train','tune','calibration','validation')])
            data=cache[seed]
            manifest=pd.read_csv(cell/'partition_manifest.csv',dtype={'row_id':str})
            if not manifest.row_id.isin(data.index).all():
                raise ValueError(f'manifest IDs absent from development splits: {cell}')
            if manifest.row_id.duplicated().any():
                raise ValueError(f'duplicate manifest ID: {cell}')
            joined=manifest.join(data,on='row_id',validate='one_to_one')
            for split,sg in joined.groupby('split',sort=False):
                pooled=sg
                pool_prev=float((pooled.income=='>50K').mean())
                pool_age=float(pooled.age.mean());pool_edu=float(pooled['education-num'].mean())
                for client,g in sg.groupby('client',sort=True):
                    tv={}
                    for col in CATEGORICAL:
                        cats=schema['categories'][col]
                        a1=g[col].value_counts(normalize=True).reindex(cats,fill_value=0)
                        b1=pooled[col].value_counts(normalize=True).reindex(cats,fill_value=0)
                        tv[col]=float(.5*np.abs(a1-b1).sum())
                        coverage.append({'cell':cell.name,'split':split,'client':client,
                            'column':col,'observed_categories':int(g[col].nunique()),
                            'declared_categories':len(cats),
                            'public_vocab_coverage':float(g[col].nunique()/len(cats)),
                            'tv_from_pooled_split':tv[col]})
                    rows.append({'cell':cell.name,'generator':cfg['generator'],
                        'partition':cfg['partition'],'k':cfg['k'],'seed':seed,
                        'split':split,'client':client,'rows':len(g),
                        'income_high_prevalence':float((g.income=='>50K').mean()),
                        'income_prevalence_abs_gap_from_pooled':abs(float((g.income=='>50K').mean())-pool_prev),
                        'age_mean':float(g.age.mean()),
                        'age_mean_abs_gap_public_range':abs(float(g.age.mean())-pool_age)/100,
                        'education_num_mean':float(g['education-num'].mean()),
                        'education_mean_abs_gap_public_range':abs(float(g['education-num'].mean())-pool_edu)/16,
                        'max_categorical_tv_from_pooled':max(tv.values()),
                        'highest_tv_column':max(tv,key=tv.get),
                        'female_high_income_count':int(((g.sex=='Female')&(g.income=='>50K')).sum()),
                        'amer_indian_eskimo_count':int((g.race=='Amer-Indian-Eskimo').sum()),
                        'non_us_native_country_count':int((g['native-country']!='United-States').sum()),
                        'question_mark_cell_count':int((g[list(CATEGORICAL)]=='?').sum().sum())})
    pd.DataFrame(rows).to_csv(a.out/'client_split_summary.csv',index=False)
    pd.DataFrame(coverage).to_csv(a.out/'category_coverage.csv',index=False)
    print(f'audited {len(set(x["cell"] for x in rows))} cells, {len(rows)} client splits')

if __name__=='__main__':main()
