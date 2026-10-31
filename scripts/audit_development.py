"""Audit development Exp 1/2 cells without looking at official Adult test."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--roots', nargs='+', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows, cells = [], []
    for root in args.roots:
        for cell in sorted(root.iterdir()):
            if not cell.is_dir() or not (cell/'exp01_complete.json').exists():
                continue
            cfg = json.loads((cell/'configuration.json').read_text())
            if cfg['reference_role'] != 'development_assessment':
                raise ValueError(f'official confirmation cell excluded: {cell}')
            part = json.loads((cell/'partition.json').read_text())
            alpha = np.asarray(part['alpha'], dtype=float)
            validation = pd.read_csv(cell/'exp01_validation.csv').set_index('method')
            assessment = pd.read_csv(cell/'exp01_test.csv')
            fits = json.loads((cell/'weight_fits.json').read_text())
            selected = json.loads((cell/'selection_frozen.json').read_text())['method']
            solver = json.loads((cell/'exp02_oracle.json').read_text())['solver']
            status = json.loads((cell/'STATUS.json').read_text())
            cells.append({'cell':cell.name,'root':str(root),'generator':cfg['generator'],
                          'partition':cfg['partition'],'clients':cfg['k'],'seed':cfg['seed'],
                          'code_hash':cfg['code_hash'],'reference_role':cfg['reference_role'],
                          'selected_within_cell':selected,'cell_status':status['status'],
                          'oracle_lp_success':solver['success'],
                          'likelihood_kind':fits['likelihood_kind'],
                          'likelihood_floor_count':fits['likelihood_floor_count'],
                          'n_assessment_repeats':int(assessment.replicate.nunique())})
            for fit in fits['methods']:
                method = fit['method']
                if not fit['success'] or method not in validation.index:
                    rows.append({'cell':cell.name,'method':method,'fit_success':False})
                    continue
                w = np.asarray(fit['weights'], dtype=float)
                a = assessment.loc[assessment.method == method]
                v = validation.loc[method]
                rows.append({'cell':cell.name,'generator':cfg['generator'],
                             'partition':cfg['partition'],'clients':cfg['k'],'seed':cfg['seed'],
                             'code_hash':cfg['code_hash'],'method':method,
                             'access':fit['access'],'fit_success':True,
                             'selected_within_cell':method == selected,
                             'validation_query_linf':float(v.query_linf),
                             'validation_unseen_query_mae':float(v.unseen_query_mae),
                             'assessment_query_linf_mean':float(a.query_linf.mean()),
                             'assessment_query_linf_sd_synthetic':float(a.query_linf.std()),
                             'assessment_unseen_query_mae_mean':float(a.unseen_query_mae.mean()),
                             'assessment_repeats':len(a),
                             'weight_l1_from_target_alpha':float(np.abs(w-alpha).sum()),
                             'effective_client_count':float(1/np.sum(w*w)),
                             'zero_weight_clients':int(np.sum(w < 1e-8)),
                             'weights_json':json.dumps(w.tolist())})
    pd.DataFrame(rows).to_csv(args.out/'method_audit.csv', index=False)
    pd.DataFrame(cells).to_csv(args.out/'cell_audit.csv', index=False)
    print(f'audited {len(cells)} development cells and {len(rows)} method fits')

if __name__ == '__main__':
    main()
