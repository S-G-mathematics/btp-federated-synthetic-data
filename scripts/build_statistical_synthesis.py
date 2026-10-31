"""Descriptive paired analysis of saved evidence; no fitting or holdout rescoring."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/statistical_synthesis'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {
        'adult_development': 'reports/representation_constrained_projected_v2_deterministic_20261024/cell_method_means.csv',
        'adult_confirmation': 'reports/final_build/confirmation_paired_cells.csv',
        'bank_external': 'reports/external_replication/paired_differences.csv',
    }
    frames = []
    provenance = {}
    for stage, path in sources.items():
        source = ROOT / path
        frame = pd.read_csv(source)
        provenance[stage] = {'path': path, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        if stage == 'adult_development':
            frame = frame[(frame.method == 'constrained') & frame.generator.isin(['copula', 'chow_liu', 'mixed_gmm'])].copy()
            frame = frame.rename(columns={'paired_delta_vs_size': 'delta', 'query_linf_mean': 'challenger_loss', 'size_query_linf_mean': 'size_loss'})
        else:
            frame = frame.rename(columns={'constrained_minus_size': 'delta', 'size': 'size_loss', 'constrained': 'challenger_loss', 'constrained_query_minimax': 'challenger_loss'})
        if 'generator' not in frame:
            frame['generator'] = 'copula'
        frame['stage'] = stage
        frame['source_path'] = path
        frame['relative_change_percent'] = 100 * frame.delta / frame.size_loss
        if frame.duplicated(['generator', 'partition', 'k', 'seed']).any():
            raise ValueError('Duplicate cell key: ' + stage)
        frames.append(frame)
    cells = pd.concat(frames, ignore_index=True)
    assert cells.groupby('stage').size().to_dict() == {'adult_confirmation': 12, 'adult_development': 54, 'bank_external': 12}
    assert np.allclose(cells.delta, cells.challenger_loss-cells.size_loss)
    cells.to_csv(OUT/'paired_cells.csv', index=False)

    def summarize(group):
        d = group.delta
        return {'cells': len(group), 'mean_size_loss': group.size_loss.mean(),
                'mean_challenger_loss': group.challenger_loss.mean(), 'mean_delta': d.mean(),
                'median_delta': d.median(), 'q25_delta': d.quantile(.25), 'q75_delta': d.quantile(.75),
                'min_delta': d.min(), 'max_delta': d.max(), 'improved_cells': int((d<0).sum()),
                'adverse_cells': int((d>0).sum()), 'practical_gain_cells': int((d<=-.005).sum()),
                'deterioration_at_least_005_cells': int((d>=.005).sum()),
                'ratio_of_mean_losses_percent_change': 100*(group.challenger_loss.mean()/group.size_loss.mean()-1)}
    overall = pd.DataFrame([dict(stage=s, **summarize(g)) for s,g in cells.groupby('stage')])
    slices = pd.DataFrame([dict(zip(['stage','generator','partition','k'], key), **summarize(g))
                           for key,g in cells.groupby(['stage','generator','partition','k'])])
    generators = pd.DataFrame([dict(stage=s,generator=f,**summarize(g)) for (s,f),g in cells.groupby(['stage','generator'])])
    overall.to_csv(OUT/'stage_summary.csv',index=False)
    slices.to_csv(OUT/'slice_summary.csv',index=False)
    generators.to_csv(OUT/'generator_summary.csv',index=False)
    (OUT/'provenance.json').write_text(json.dumps({'inputs':provenance,'analysis':'post-experiment descriptive analysis; no reselection','missing_values':'not applicable or unavailable; never imputed','uncertainty':'quantiles and ranges describe registered cells; no population confidence intervals'},indent=2)+'\n')
    lines = ['# What the saved results establish', '',
             'This synthesis is a post-experiment descriptive analysis of saved cell means. It does not change selection, score new people, or rerun generators. Each cell averages its registered synthetic draws. Negative challenger-minus-size differences favour constrained weighting.', '',
             '| Evidence stage | Cells | Size loss | Challenger loss | Mean difference | Median difference | Improved cells | Gain ≥0.005 cells |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in overall.itertuples():
        lines.append(f'| {r.stage} | {r.cells} | {r.mean_size_loss:.6f} | {r.mean_challenger_loss:.6f} | {r.mean_delta:+.6f} | {r.median_delta:+.6f} | {r.improved_cells} | {r.practical_gain_cells} |')
    lines += ['', 'Cell win counts above are descriptive, and are distinct from the registered practical-gain decision on seed-averaged slices. The registered slice counts remain 0/18 Adult development, 0/6 Adult official holdout, and 0/4 Bank external. A favourable individual cell does not establish a qualifying slice or global method.', '',
              '## Generator dependence', '', '| Stage | Generator | Cells | Mean difference | Median difference | Observed range |', '| --- | --- | ---: | ---: | ---: | --- |']
    for r in generators.itertuples():
        lines.append(f'| {r.stage} | {r.generator} | {r.cells} | {r.mean_delta:+.6f} | {r.median_delta:+.6f} | [{r.min_delta:+.6f}, {r.max_delta:+.6f}] |')
    lines += ['', '## Statistical interpretation', '',
              '- Means summarize the fixed registered design with equal weight per cell. They do not estimate performance across a random population of federated tasks.',
              '- Medians, quartiles and observed ranges reveal heterogeneity. Ranges are not confidence intervals. The ratio of mean losses in the CSV is descriptive and differs from averaging cell-relative changes.',
              '- Adult cells reuse people, partitions and model families. Synthetic draws share checkpoints. Bank contacts may share individuals. No p-value or narrow independent-cell confidence interval is justified by treating these records as independent cohorts.',
              '- The registered 0.005 margin is operational. Failure to reach it does not establish equivalence, zero benefit, or universal optimality of size weights.',
              '- No omnibus mean combines development, official holdout and Bank. They have different roles and workloads. Viewed development diagnostics remain exploratory.',
              '', '## Mechanisms and adverse results', '',
              'The female conditional has a measured sex/relationship dependency failure: mean feature-query maximum 0.375, with relationship=Husband the worst query in all twelve confirmation cells. Requested-condition compliance does not validate other features. Rare-condition abstentions and poor conditional students remain in the evidence.', '',
              'Logistic TSTR Brier 0.129818 versus privileged TRTR 0.101987 is a registered-budget comparison. Real train/tune/calibration sizes are 21,148/4,880/3,254; synthetic sizes are 10,000/2,000/2,000. These results cannot establish an intrinsic difference at matched sample sizes.', '',
              'Finite-pilot LP certificates apply to their saved matrices and targets. Schema projection, local-model quality, summary access and target-mass constraints explain different parts of the observed behavior; historical changes that alter several parts together are not isolated causal ablations.', '',
              'The main pipeline remains nonprivate. Conditional histogram and adapted FLAIM accounting apply only to their declared releases and assumptions. Model/raw application payload ratios of 1.915–2.866 do not support a compression claim or a WAN traffic estimate.', '',
              '## Inspect and reproduce', '',
              '- [All paired cells](../reports/statistical_synthesis/paired_cells.csv)',
              '- [Every slice and its range](../reports/statistical_synthesis/slice_summary.csv)',
              '- [Generator summaries](../reports/statistical_synthesis/generator_summary.csv)',
              '- [Input hashes and analysis scope](../reports/statistical_synthesis/provenance.json)',
              '- [Conditional evidence](../AUTHOR_READY/PAPER_TABLES/female_dependency_worst_query.csv)',
              '- [Utility budgets](../AUTHOR_READY/PAPER_TABLES/utility_with_registered_budgets.csv)',
              '- [Twelve-package acceptance](../AUTHOR_READY/TWELVE_PACKAGE_ACCEPTANCE.md)', '',
              'Run `python scripts/build_statistical_synthesis.py`. Only saved CSV files are read.']
    (ROOT/'docs/RESULTS_AND_STATISTICAL_INFERENCE.md').write_text('\n'.join(lines)+'\n')
    print(overall.to_string(index=False))


if __name__ == '__main__':
    main()
