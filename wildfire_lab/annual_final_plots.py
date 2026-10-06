"""Figures from frozen reused-year predictions and saved Gram diagnostics."""

from collections import defaultdict
import json

import matplotlib.pyplot as plt
import numpy as np

from wildfire_lab.annual_plots import style, save, TEAL, ORANGE, INK

MODELS = [('training_mean', 'Training mean', '#8c999e'),
          ('linear_year_trend', 'Year trend', '#b3c1c5'),
          ('matched_rbf_svr_4', 'RBF · 4 inputs', TEAL),
          ('matched_fidelity_svr_4', 'QSVR · 4 qubits', ORANGE),
          ('matched_rbf_svr_10', 'RBF · 10 inputs', '#54969b'),
          ('matched_fidelity_svr_10', 'QSVR · 10 qubits', '#dca16b')]


def predictions(rows, output):
    figure, axes = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[2, 1])
    actual = rows['training_mean']['actual_ha']
    years = rows['training_mean']['years']
    axes[0].plot(years, actual, color=INK, marker='o', lw=2, label='Observed annual mean')
    for identifier, label, color in MODELS[:4]:
        axes[0].plot(years, rows[identifier]['predicted_ha'], color=color, marker='.', lw=1.6, label=label)
    axes[0].set_title('Annual swings remain poorly predicted', loc='left', weight='bold', fontsize=19)
    axes[0].set_ylabel('Reported hectares / fire')
    axes[0].set_ylim(0, 730)
    axes[0].legend(frameon=False, ncol=2, fontsize=10)
    axes[0].grid(axis='y', alpha=.15)
    for identifier, label, color in MODELS[2:]:
        axes[1].plot(years, rows[identifier]['predicted_ha'], color=color, marker='o', lw=1.5, label=label)
    axes[1].set_ylabel('Prediction detail')
    axes[1].set_ylim(0, 140)
    axes[1].set_xlabel('Reused evaluation years · 2019–2024')
    axes[1].legend(frameon=False, ncol=2, fontsize=10)
    axes[1].grid(axis='y', alpha=.15)
    figure.tight_layout()
    save(figure, output, 'annual-reused-predictions')


def year_errors(rows, output):
    figure, axis = plt.subplots(figsize=(11, 5.5))
    values = np.array([rows[name]['absolute_errors_ha'] for name, _, _ in MODELS])
    image = axis.imshow(values, cmap='YlOrBr', vmin=0, vmax=660, aspect='auto')
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            axis.text(j, i, f'{value:.1f}', ha='center', va='center', color='white' if value > 430 else INK)
    axis.set_yticks(range(len(MODELS)), [f"{label}  ·  MAE {rows[name]['mae_ha']:.1f}" for name,label,_ in MODELS])
    axis.set_xticks(range(6), rows['training_mean']['years'])
    axis.set_title('Every reused-year error', loc='left', weight='bold', fontsize=19, pad=18)
    axis.set_xlabel('Absolute error · reported hectares per fire')
    figure.colorbar(image, ax=axis, label='Absolute error (ha/fire)', shrink=.85)
    figure.tight_layout()
    save(figure, output, 'annual-reused-errors')


def spectra(diagnostics, output):
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    offsets = [(8, 8), (12, -24), (-108, 24), (8, 8)]
    for entry, (_, label, color), offset in zip(diagnostics[:4], MODELS[2:], offsets):
        axes[0].plot(range(1, 32), sorted(entry['eigenvalues'], reverse=True), color=color, lw=1.8, label=label)
        axes[1].scatter(entry['off_diagonal_mean'], entry['cross_mean'], color=color, s=90)
        axes[1].annotate(label, (entry['off_diagonal_mean'], entry['cross_mean']), xytext=offset, textcoords='offset points', fontsize=9,
                         arrowprops=dict(arrowstyle='-', color=color, lw=.7))
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Eigenvalue rank · 31 training years')
    axes[0].set_ylabel('Raw Gram eigenvalue')
    axes[0].legend(frameon=False, fontsize=9)
    axes[1].set_xscale('log')
    axes[1].set_yscale('log')
    axes[1].set_xlim(.0004, .3)
    axes[1].set_ylim(.0004, .3)
    axes[1].set_xlabel('Mean off-diagonal training similarity')
    axes[1].set_ylabel('Mean reused-year → training similarity')
    for axis in axes:
        axis.grid(alpha=.15)
    figure.suptitle('Stable matrices can still carry little cross-year similarity', x=.06, ha='left', fontsize=17, weight='bold')
    figure.tight_layout()
    save(figure, output, 'annual-final-kernels')


def crossover(records, baseline, output):
    values = defaultdict(list)
    selectors = []
    for row in records:
        if row.get('status') != 'complete':
            continue
        if row['selector'] not in selectors:
            selectors.append(row['selector'])
        values[row['selector'], row['kind']].append(row['mae_ha'])
    kinds = ['ridge', 'rbf', 'quantum']
    table = np.array([[np.mean(values[name,kind]) for kind in kinds] for name in selectors])
    figure, axis = plt.subplots(figsize=(9, 6))
    image = axis.imshow(table-baseline, cmap='YlOrBr', vmin=0, vmax=35, aspect='auto')
    for i,row in enumerate(table):
        for j,value in enumerate(row):
            axis.text(j, i, f'{value:.1f}', ha='center', va='center',
                      color='white' if value-baseline > 22 else INK)
    axis.set_yticks(range(len(selectors)), [name.replace('_', ' ') for name in selectors])
    axis.set_xticks(range(3), ['Fixed ridge', 'Fixed RBF-SVR', 'Fixed QSVR'])
    axis.set_title('Selection × prediction · all frozen combinations', loc='left', fontsize=16, weight='bold', pad=20)
    figure.colorbar(image, ax=axis, label='MAE above training mean (ha/fire)', shrink=.8)
    figure.text(.12, .02, f'Cells: mean MAE across three reused-year sensitivity seeds. Training mean: {baseline:.1f}.\nAll-ten is a different input budget; repeated years/seeds are not independent replications.', fontsize=9)
    figure.tight_layout(rect=(0,.08,1,1))
    save(figure, output, 'annual-final-crossover')


def generate(root, output):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    style()
    outcome = json.loads((root/'docs/results/annual-final.json').read_text())
    audit = json.loads((root/'docs/results/annual-final-audit.json').read_text())
    rows = {row['id']:row for row in outcome['main_results']}
    predictions(rows, output)
    year_errors(rows, output)
    spectra(audit['kernel_diagnostics'], output)
    crossover(outcome['crossed_results'], rows['training_mean']['mae_ha'], output)
    return dict(figures=4, files=8, predictor_fits=0, quantum_states=0, reused_years=True)
