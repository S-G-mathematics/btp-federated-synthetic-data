"""Rebuild final empirical tables and scientific plots from saved artifacts only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/final_build'


def load(relative: str) -> pd.DataFrame:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f'Required immutable report artifact absent: {relative}')
    return pd.read_csv(path)


def savefig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=180, bbox_inches='tight', metadata={'Software': 'BTP saved-artifact report builder'})
    plt.close()


def adult_development() -> dict:
    slices = load('reports/representation_constrained_projected_v2_deterministic_20261024/slice_summary.csv')
    frame = slices[(slices.method == 'constrained') &
                   (slices.generator.isin(('copula','chow_liu','mixed_gmm')))].sort_values(['generator','partition','k'])
    if len(frame) != 18 or int(frame.practical_mean_gain.sum()) != 0:
        raise ValueError('Corrected Adult 18-slice decision no longer reproduces')
    fig, ax = plt.subplots(figsize=(9, 7))
    labels = [f'{r.generator} / {r.partition} / K{r.k}' for r in frame.itertuples()]
    values = frame.mean_paired_delta.to_numpy()
    colors = ['#C95545' if v > 0 else '#376B9B' for v in values]
    ax.barh(np.arange(len(frame)), values, color=colors)
    ax.set_yticks(np.arange(len(frame)), labels)
    ax.axvline(-.005, ls='--', color='black', label='registered practical gain')
    ax.axvline(0, color='gray', lw=.7)
    ax.set_xlabel('Constrained minus size query-max; lower favours constrained')
    ax.set_title('Adult corrected development: 18 registered slices')
    ax.legend(loc='lower right')
    savefig('adult_18_slice_differences.png')
    return {'slices': 18, 'practical_gain_slices': 0,
            'mean_paired_delta': float(frame.mean_paired_delta.mean())}


def external() -> dict:
    frame = load('reports/external_replication/slice_decisions.csv')
    fig, ax = plt.subplots(figsize=(7, 3.5))
    x = np.arange(len(frame))
    labels = [f'{r.generator}/{r.partition}' for r in frame.itertuples()]
    delta_col = 'mean_constrained_minus_size'
    ax.bar(x, frame[delta_col], color=['#C95545' if v > 0 else '#376B9B' for v in frame[delta_col]])
    ax.axhline(-.005, ls='--', color='black')
    ax.axhline(0, color='gray', lw=.7)
    ax.set_xticks(x, labels, rotation=30, ha='right')
    ax.set_ylabel('Constrained minus size query-max')
    ax.set_title('Official UCI Bank external replication: four three-seed slices')
    savefig('bank_external_slice_differences.png')
    return {'slices': len(frame), 'mean_paired_delta': float(frame[delta_col].mean())}


def sampling() -> None:
    for relative, xcol, ycol, title, output in (
        ('reports/projected_sample_size_20261024/by_family.csv', 'm', 'size_query_mean',
         'Adult size-weight fidelity versus synthetic row count', 'synthetic_size_curve.png'),
        ('reports/projected_pilot_sensitivity_v2_20261024/by_family.csv', 'pilot_per_client', 'H_error_mean',
         'Fixed-pilot query matrix error versus pilot size', 'pilot_size_curve.png'),
    ):
        path = ROOT / relative
        if not path.exists():
            # A missing panel is explicit in the build summary, never fabricated.
            continue
        frame = pd.read_csv(path)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for name, group in frame.groupby('family'):
            ax.plot(group[xcol], group[ycol], marker='o', label=name)
        ax.set_xlabel(xcol)
        ax.set_ylabel(ycol)
        ax.set_title(title)
        ax.legend(fontsize=8)
        savefig(output)


def mechanisms() -> None:
    projected = load('reports/mechanisms/projection_summary.csv')
    if {'generator','mean_raw_loss','mean_projected_loss'} <= set(projected):
        table = projected[projected.method == 'size'].groupby('generator')[['mean_raw_loss','mean_projected_loss']].mean()
        table.plot.bar(figsize=(6,4), rot=0)
        plt.ylabel('Mean primary query-max')
        plt.title('Same-row structural projection mechanism')
        savefig('structural_projection_effect.png')
    severity = load('reports/mechanisms/severity_cell_means.csv')
    if {'severity','method','query_linf_mean'} <= set(severity):
        table = severity.groupby(['severity','method']).query_linf_mean.mean().unstack()
        table.plot.bar(figsize=(6,4), rot=0)
        plt.ylabel('Mean primary query-max')
        plt.title('Fixed quantity: two non-IID severity settings')
        savefig('heterogeneity_severity.png')


def references() -> dict:
    pgm = load('reports/published_references/pgm_cell_means.csv')
    flaim = load('reports/published_references/flaim_cell_means.csv')
    both = pgm[['cell','partition','k','seed','pgm_minus_size_mean']].sort_values(['partition','k','seed']).copy()
    both['flaim_minus_size_mean'] = flaim.sort_values(['partition','k','seed']).flaim_minus_size_mean.to_numpy()
    both.to_csv(OUT / 'reference_cell_differences.csv', index=False)
    labels = [f'{r.partition}/K{r.k}/s{r.seed}' for r in both.itertuples()]
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(both))
    ax.bar(x-.18, both.pgm_minus_size_mean, width=.36, label='Nonprivate same-summary PGM')
    ax.bar(x+.18, both.flaim_minus_size_mean, width=.36, label='FLAIM; different privacy/access')
    ax.axhline(0, color='gray', lw=.7)
    ax.set_xticks(x, labels, rotation=25, ha='right')
    ax.set_ylabel('Reference minus nonprivate size query-max')
    ax.set_title('Published code references: access labels differ')
    ax.legend(fontsize=8)
    savefig('published_reference_differences.png')
    return {'pgm_cells': len(pgm), 'flaim_cells': len(flaim),
            'pgm_mean_minus_size': float(pgm.pgm_minus_size_mean.mean()),
            'flaim_mean_minus_size': float(flaim.flaim_minus_size_mean.mean())}


def resources() -> None:
    frame = load('reports/resources/matched_raw_vs_model_payloads.csv')
    cells = frame.groupby('cell')[['raw_table_bytes','model_plus_metadata_bytes']].sum()
    cells.index = [x.split('_s101')[0] for x in cells.index]
    cells.plot.bar(figsize=(8, 4), rot=20)
    plt.ylabel('pickle5+gzip6 application payload bytes')
    plt.title('Copula model releases versus same-format raw tables')
    savefig('matched_payload_bytes.png')


def secondary_development() -> None:
    frontier = load('reports/representation_constrained_projected_v2_deterministic_20261024/cell_method_means.csv')
    fig, ax = plt.subplots(figsize=(6,4))
    for generator, group in frontier.groupby('generator'):
        ax.scatter(group.weight_l1_from_alpha, group.query_linf_mean,
                   label=generator, alpha=.65, s=25)
    ax.set_xlabel('Generator mass L1 distance from fixed alpha')
    ax.set_ylabel('Empirical primary query-max')
    ax.set_title('Adult development fidelity versus client-mass shift')
    ax.legend(fontsize=8)
    savefig('fidelity_vs_target_mass_shift.png')

    query = load('reports/projected_query_audit_20261025/arity_support_summary.csv')
    query = query.groupby(['workload','arity','support_stratum'], as_index=False).agg(
        size_abs_error_mean=('size_abs_error_mean','mean'),
        constrained_abs_error_mean=('constrained_abs_error_mean','mean'))
    query.to_csv(OUT / 'query_arity_support_summary.csv', index=False)
    common = query[query.workload == 'primary']
    labels = [f'{r.arity}way/{r.support_stratum}' for r in common.itertuples()]
    fig, ax = plt.subplots(figsize=(9,4))
    x = np.arange(len(common))
    ax.bar(x-.2, common.size_abs_error_mean, width=.4, label='size')
    ax.bar(x+.2, common.constrained_abs_error_mean, width=.4, label='constrained')
    ax.set_xticks(x, labels, rotation=35, ha='right')
    ax.set_ylabel('Mean absolute query error')
    ax.set_title('Primary query arity and real-support strata')
    ax.legend()
    savefig('query_arity_support.png')

    utility = load('reports/projected_secondary_20261024/utility_global_by_cell.csv')
    utility = utility.groupby(['learner','method'], as_index=False).brier.mean()
    utility.to_csv(OUT / 'development_utility_summary.csv', index=False)
    table = utility.pivot(index='learner', columns='method', values='brier')
    table.plot.bar(figsize=(7,4), rot=0)
    plt.ylabel('Alpha-weighted Brier (lower better)')
    plt.title('Development TSTR and privileged TRTR')
    savefig('development_utility_brier.png')

    condition = load('reports/projected_conditionals_v2_20261024/route_summary.csv')
    condition = condition[condition.method == 'size']
    labels = [f'{r.family}/{r.condition}' for r in condition.itertuples()]
    fig, ax = plt.subplots(figsize=(9,5))
    x = np.arange(len(condition))
    ax.bar(x-.2, condition.direct_query_linf_mean, width=.4, label='teacher rejection')
    ax.bar(x+.2, condition.student_query_linf_mean, width=.4, label='trained per-condition student')
    ax.set_xticks(x, labels, rotation=45, ha='right')
    ax.set_ylabel('Conditional query-max')
    ax.set_title('Supported registered development conditions')
    ax.legend()
    savefig('conditional_student_teacher.png')

    joint = load('reports/projected_joint_prediction_20261025/global_summary.csv')
    joint = joint[(joint.joint_method == 'size') & joint.predictor.isin(('joint_implied','synthetic_logistic','TRTR_privileged_logistic'))]
    if len(joint):
        joint.pivot(index='family', columns='predictor', values='brier_mean').plot.bar(figsize=(7,4), rot=0)
        plt.ylabel('Brier (lower better)')
        plt.title('Joint-implied versus synthetic-trained and real-trained')
        savefig('joint_vs_trained_predictor.png')

    privacy = load('reports/public_atom_privacy_20261024/by_family.csv')
    privacy.pivot(index='family', columns='method', values='query_linf_mean').plot.bar(figsize=(8,4), rot=0)
    plt.ylabel('Empirical primary query-max')
    plt.title('Separate atom-aware histogram: private and matched nonprivate')
    savefig('public_atom_histogram_utility.png')


def confirmation() -> dict:
    source = ROOT / 'results/adult_confirmation_20261025'
    cells = sorted(source.glob('*/primary_draw_metrics.csv'))
    if len(cells) != 12:
        return {'status': 'incomplete', 'completed_primary_cells': len(cells)}
    draws = pd.concat([pd.read_csv(path).assign(cell=path.parent.name) for path in cells], ignore_index=True)
    if len(draws) != 12*3*5:
        raise ValueError('Confirmation draw count mismatch')
    draws.to_csv(OUT / 'confirmation_all_draws.csv', index=False)
    all_answers = pd.concat([pd.read_csv(path).assign(cell=path.parent.name)
                             for path in sorted(source.glob('*/per_query_answers.csv'))], ignore_index=True)
    if len(all_answers) == 0:
        raise ValueError('Confirmation query answers absent')
    maxima = (all_answers[all_answers.workload == 'primary_v2']
        .sort_values(['cell','method','replicate','absolute_error','query'],
                     ascending=[True,True,True,False,True])
        .groupby(['cell','method','replicate'], as_index=False).first())
    maxima.to_csv(OUT / 'confirmation_dominant_queries.csv', index=False)
    check = draws.merge(maxima[['cell','method','replicate','absolute_error']],
                        on=['cell','method','replicate'], validate='one_to_one')
    if np.max(np.abs(check.query_linf-check.absolute_error)) > 1e-12:
        raise ValueError('Named confirmation primary query does not reproduce maximum')
    all_answers['alpha_pooled_reference_gap'] = (all_answers.real_alpha-all_answers.real_pooled_secondary).abs()
    query_summary = all_answers.groupby(['workload','query','method'], as_index=False).agg(
        mean_absolute_error=('absolute_error','mean'),
        max_absolute_error=('absolute_error','max'),
        mean_alpha_pooled_reference_gap=('alpha_pooled_reference_gap', 'mean'))
    query_summary.to_csv(OUT / 'confirmation_query_summary.csv', index=False)
    means = draws.groupby(['cell','partition','k','seed','method'], as_index=False).agg(
        query_linf_mean=('query_linf','mean'), audit_linf_mean=('unseen_query_linf','mean'),
        weight_l1=('weight_l1','first'))
    means.to_csv(OUT / 'confirmation_cell_means.csv', index=False)
    wide = means.pivot(index=['cell','partition','k','seed'], columns='method', values='query_linf_mean').reset_index()
    wide['constrained_minus_size'] = wide.constrained-wide['size']
    wide['uniform_minus_size'] = wide.uniform-wide['size']
    wide.to_csv(OUT / 'confirmation_paired_cells.csv', index=False)
    slice_table = wide.groupby(['partition','k'], as_index=False).agg(
        constrained_minus_size=('constrained_minus_size','mean'),
        uniform_minus_size=('uniform_minus_size','mean'),
        size_query_linf=('size','mean'))
    slice_table.to_csv(OUT / 'confirmation_slices.csv', index=False)
    fig, ax = plt.subplots(figsize=(7,4))
    x = np.arange(len(slice_table))
    labels = [f'{r.partition}/K{r.k}' for r in slice_table.itertuples()]
    ax.bar(x-.18, slice_table.constrained_minus_size, width=.36, label='constrained − size')
    ax.bar(x+.18, slice_table.uniform_minus_size, width=.36, label='uniform − size')
    ax.axhline(-.005, ls='--', color='black', label='practical gain')
    ax.axhline(0, color='gray', lw=.7)
    ax.set_xticks(x, labels, rotation=25, ha='right')
    ax.set_ylabel('Paired primary query-max difference')
    ax.set_title('Frozen Adult official-test confirmation')
    ax.legend(fontsize=8)
    savefig('adult_frozen_confirmation.png')
    utility_files = sorted(source.glob('*/utility_metrics.csv'))
    conditional_files = sorted(source.glob('*/conditional_metrics.csv'))
    if len(utility_files) == 12:
        util = pd.concat([pd.read_csv(path).assign(cell=path.parent.name) for path in utility_files], ignore_index=True)
        util.to_csv(OUT / 'confirmation_utility.csv', index=False)
        globals_only = util[util.scope == 'global_alpha']
        paired = globals_only.pivot(index=['cell','learner'], columns='method', values=['brier','auroc'])
        paired.columns = [f'{metric}_{method}' for metric, method in paired.columns]
        paired = paired.reset_index()
        paired['brier_size_minus_trtr'] = paired.brier_size-paired.brier_trtr_privileged
        paired['brier_constrained_minus_size'] = paired.brier_constrained-paired.brier_size
        paired['auroc_size_minus_trtr'] = paired.auroc_size-paired.auroc_trtr_privileged
        paired.to_csv(OUT / 'confirmation_utility_paired.csv', index=False)
    if len(conditional_files) == 12:
        cond = pd.concat([pd.read_csv(path).assign(cell=path.parent.name) for path in conditional_files], ignore_index=True)
        cond.to_csv(OUT / 'confirmation_conditional.csv', index=False)
    if len(utility_files) != 12 or len(conditional_files) != 12:
        raise ValueError('Frozen secondary confirmation incomplete')
    return {'status': 'complete', 'completed_primary_cells': 12,
            'overall_constrained_minus_size': float(wide.constrained_minus_size.mean()),
            'overall_size_query_linf': float(wide['size'].mean()),
            'utility_cells': len(utility_files), 'conditional_cells': len(conditional_files)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true', required=True)
    ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {'adult_development': adult_development(), 'bank_external': external(),
               'references': references()}
    sampling()
    mechanisms()
    resources()
    secondary_development()
    summary['confirmation'] = confirmation()
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
