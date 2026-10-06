"""Render descriptive hardware figures/report from saved, collected evidence only."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.saved_hardware_selector import audit
from wildfire_lab.saved_hardware_kernels import audit_shards


def load(name):
    return json.loads((ROOT/'docs/results'/name).read_text())


def figures(selectors,kernels):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.titleweight':'bold'})
    fig,axes = plt.subplots(2,2,figsize=(12,9),layout='constrained')
    colors = {'raw':'#18696d','dd_twirl':'#b76832'}
    for arm in colors:
        for policy,style in [('uniform','--'),('optimized2','-')]:
            rows = [r for r in selectors['rows'] if r['arm']==arm and r['policy']==policy]
            axes[0,0].plot([r['pool_size'] for r in rows],[100*r['feasible_fraction'] for r in rows],
                           style,color=colors[arm],marker='o',label=arm.replace('_',' ')+' / '+policy)
    axes[0,0].set(title='Measured four-feature acceptance',xlabel='Candidate bits (+ three ancillas)',
                  ylabel='Valid physical shots (%)',xticks=[10,16,20],ylim=(-1,25))
    axes[0,0].legend(fontsize=8)
    for policy in ['uniform','optimized2']:
        records = [r for r in selectors['compiled_records'][:6] if r['label']['policy']==policy]
        axes[0,1].plot([r['label']['pool_size'] for r in records],
                      [r['operations'].get('cz',0) for r in records],marker='o',label=policy)
    axes[0,1].set(title='Preparation and native gate cost',xlabel='Candidate bits',ylabel='Compiled CZ gates',xticks=[10,16,20])
    axes[0,1].legend(fontsize=8)
    keys = list(kernels['shards'])
    labels = ['raw selector / '+k.split('-')[1] if k.startswith('raw-')
              else 'DD selector / '+k.split('-')[1] for k in keys]
    positions = np.arange(len(keys))
    ideal = [next(r['mae_ha'] for r in s['models'][key]['rows'] if r['model']=='qsvr')
             for key,s in kernels['shards'].items()]
    axes[1,0].plot(positions,ideal,'k--o',label='Analytic reference')
    for arm,color in colors.items():
        rows = [next(r for r in s['rows'] if r['kernel_arm']==arm and r['label']=='raw')
                for s in kernels['shards'].values()]
        axes[1,0].plot(positions,[r['mae_ha'] for r in rows],color=color,marker='o',label=arm.replace('_',' '))
        corrected = [next(r for r in s['rows'] if r['kernel_arm']==arm and r['label']=='readout_psd')
                     for s in kernels['shards'].values()]
        axes[1,1].scatter([r['train_kernel_rmse'] for r in rows],[r['mae_ha'] for r in rows],
                          color=color,marker='o',label=arm+' uncorrected')
        axes[1,1].scatter([r['train_kernel_rmse'] for r in corrected],[r['mae_ha'] for r in corrected],
                          color=color,marker='x',s=60,label=arm+' readout+PSD')
    axes[1,0].set(title='Measured-kernel prediction',ylabel='MAE (ha/fire)',xticks=positions,xticklabels=labels)
    axes[1,0].tick_params(axis='x',labelrotation=25)
    axes[1,0].legend(fontsize=8)
    axes[1,1].set(title='Geometry recovery versus prediction',xlabel='Training-kernel RMSE to analytic reference',ylabel='MAE (ha/fire)')
    axes[1,1].legend(fontsize=8,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.20))
    fig.suptitle('Larger feature selection on IBM Marrakesh',fontsize=18,fontweight='bold')
    path = ROOT/'docs/figures/selector-hardware.png'
    fig.savefig(path,dpi=170)
    plt.close(fig)


def report(selectors,kernels,failure):
    selector_table = ['| Acquisition | Candidates | Circuit | Valid /512 | Counter-clean /512 | SQD gap | Matched uniform gap |',
                      '|---|---:|---|---:|---:|---:|---:|']
    for r in selectors['rows']:
        gap = f"{r['gap_to_exact']:.4f}" if 'gap_to_exact' in r else 'No sample'
        uniform = f"{r['matched_uniform_mean_gap']:.4f}" if 'matched_uniform_mean_gap' in r else '—'
        selector_table.append(f"| {r['arm']} | {r['pool_size']} | {r['policy']} | {r['feasible_shots']} | {r['clean_counter_feasible_shots']} | {gap} | {uniform} |")
    references = ['| Selector subset | Ridge | RBF-SVR | Analytic QSVR |','|---|---:|---:|---:|']
    measured = ['| Subset | Kernel acquisition | Raw | PSD | Rank4 | Readout | Readout+PSD | Readout+rank4 |',
                '|---|---|---:|---:|---:|---:|---:|---:|']
    timing_table = ['| Subset | Kernel arm | Charge(s) | Created→finished(s) | Running→finished(s) | API(s) |',
                    '|---|---|---:|---:|---:|---:|']
    for key,s in kernels['shards'].items():
        values = {r['model']:r['mae_ha'] for r in s['models'][key]['rows']}
        references.append(f"| {key} | {values['ridge']:.2f} | {values['rbf']:.2f} | {values['qsvr']:.2f} |")
        for arm in ['raw','dd_twirl']:
            values = {r['label']:r['mae_ha'] for r in s['rows'] if r['kernel_arm']==arm}
            measured.append('| '+key+' | '+arm+' | '+' | '.join(f'{values[k]:.2f}' for k in
                              ['raw','psd','rank4','readout','readout_psd','readout_rank4'])+' |')
            t = s['timings'][arm]
            timing_table.append('| '+key+' | '+arm+' | '+' | '.join(f'{t[k]:.2f}' for k in
                                ['quantum_seconds','created_to_finished_seconds','running_to_finished_seconds','submission_roundtrip_seconds'])+' |')
    charge = selectors['quantum_seconds_total']+kernels['quantum_seconds_total']+failure['charged_qpu_seconds_total']
    return f'''# Larger selectors on real IBM hardware

The 10/16/20-candidate study now has **actual Marrakesh counts and measured downstream QSVR kernels**. Ideal sampling gains did not survive uniformly: the 20-candidate optimized raw selector retained **20/512** valid four-feature samples; DD/twirling retained **zero**. More candidates create a larger search space, but preparation depth and noise are binding constraints. No quantum advantage is established.

![Counts, native gates and measured predictions](figures/selector-hardware.png)

## What was measured

First previously inspected chronological development fold only: 1988–2006 training (19 years), 2007–2010 validation (four years). Target remains annual Ontario mean reported hectares per fire. Original 2019–2024 evidence is unchanged. Candidate inclusion uses10/16/20 bits **plus three counter ancillas**; each surviving selected subset uses **four QSVR qubits**. Larger candidate pools do not provide more independent climate observations.

Frozen local p=2 QAOA parameters are reused, without hardware optimization. A polynomial conditional-count Dicke initializer prepares the uniform four-of-n state; exact small-state amplitude and Qiskit p1/p2 parity tests verify its ideal behavior. The cost unitary removes a cardinality penalty that is zero in the ideal feasible sector; noisy out-of-sector dynamics differ. The original full QUBO still scores feasible samples. Counter measurements diagnose preparation failure, not logical QEC.

Uniform-preparation circuits compile to1,277/2,364/3,057 CZ gates; optimized p2 circuits to1,739/3,371/4,860. The20-candidate p2 depth is8,566. This preparation is polynomial, but it remains too deep for robust performance here.

## Actual selection and SQD

Two raw/combined jobs, eighteen PUBs each,512 shots/PUB: **18,432 physical shots;11 charged seconds**. Independent assignment calibration uses two circuits per actual physical layout. SQD projects the original diagonal Hamiltonian onto **observed feasible states only** and checks its lowest energy against the direct sampled minimum. It adds no optimization beyond that diagonal minimum. Counter-clean means cardinality four and final ancillas zero; the predeclared SQD basis uses cardinality four, not the stricter diagnostic.

{chr(10).join(selector_table)}

Uniform controls use20 saved classical Monte Carlo seeds at the **same number of accepted draws** as each measured cell, not512 guaranteed-valid samples. At16 candidates, raw optimized sampling has a smaller objective gap than these matched controls. At20 candidates the combined run provides no subset; it is retained, never filled with simulator samples. Readout inversion reweights only the existing feasible basis, creates no new SQD states and claims no normalized full distribution. Sparse processing avoids2^n dense arrays.

## Measured kernels and fixed regressors

All five predeclared optimized subsets with valid samples are retained. A compute–uncompute circuit estimates the all-zero probability for190 upper-triangular training entries (including diagonals) and76 validation/train pairs per subset. Same train-only standardization, linear ZZ feature map, $\\theta=(\\pi/32)\\tanh(z/2)$, $C=1$ and $\\epsilon=0.2$. Model training remains classical; the QPU estimates similarities.

Matched fixed references, MAE in **ha/fire**:

{chr(10).join(references)}

Actual hardware-kernel regressors, same subsets and validation labels:

{chr(10).join(measured)}

Every variant is reported; no winner is promoted from these reused validation errors. PSD removes negative training eigenvalues and projects cross kernels onto the same positive eigenspace; rank4 additionally keeps at most four positive directions. Independent four-qubit readout inversion retains negative quasi-probability diagnostics, then clips the zero outcome to[0,1] before declared matrix repairs. Calibration is128 shots per prepared state, not an exact channel; correlated readout is not modeled. Geometry recovery and predictive recovery are distinct outcomes.

## Scheduler failure and declared correction

The original two1,332-PUB kernel jobs both failed with **1520** before circuit execution. They returned **zero counts**, with `job.usage()`0 and metrics charge2 seconds each. IBM's [error registry](https://quantum.cloud.ibm.com/docs/en/errors) explicitly recommends splitting circuits/PUBs. Their frozen plan, intents and sanitized [failure record](results/selector-hardware-kernels.json) are preserved.

Under the owner's further-job/ten-minute monthly authority, the separately frozen [sharded plan](../experiments/selector_kernel_shards.json) copies unchanged compiled circuits into ten268-PUB jobs (five subsets × two arms), capped20 seconds each. Each subset/arm gets its own two calibration circuits. No failed intent is reset, no ambiguous job is retried, and no subset is selected using prediction errors. Sharding changes temporal calibration and creates a sequential-acquisition limitation; it does not change the scientific model.

The corrected jobs return **{kernels['physical_shots']:,} shots** and support **{kernels['predictor_fits']} fixed QSVR fits**, using **{kernels['quantum_seconds_total']:.0f} charged seconds**. Expanded-study total including selectors and failures: **{charge:.0f} charged seconds**. Earlier Fez/Marrakesh/Quebec jobs used75 seconds across accounts; that is a separate comparison. Monthly instance allowance and project totals spanning accounts are distinct.

{chr(10).join(timing_table)}

Created→finished is service turnaround; running→finished is wall time, neither is charged QPU time. API roundtrip is submission overhead and polling delay is not part of these timestamp differences.

## Replay and interpretation

```sh
uv sync --locked --group data --group analysis --group quantum --group hardware --group mitigation
uv run --no-sync python scripts/pipeline.py annual selector-hardware-collect --output .cache/wildfire/hardware-public.json --execute
```

Public replay uses no credentials, service requests, fits, new states, SQD solves or random draws. It checks shot totals/bit ordering, feasibility, actual sampled diagonal minima, stored preprocessing and fitted prediction equations, all-zero probabilities, assignment matrices and declared repairs. It does not independently reproduce the physical experiment or validate service charges from private logs. [Selector counts](results/selector-hardware.json) · [Measured shards](results/selector-hardware-kernel-shards.json) · [Local sampling study](SELECTOR_SCALING.md) · [Forest source limits](FOREST_CONTEXT.md).

The useful finding is the separation of **ideal search quality, physical feasible-sample yield and downstream prediction**. Twenty candidates give4,845 four-feature subsets, but exhaustive classical enumeration is still inexpensive. One acquisition pair per subset is not statistical replication; this experiment demonstrates implementation and failure modes, not a quantum speedup, causal device ranking or operational wildfire forecast.
'''


if __name__ == '__main__':
    audit(ROOT)
    audit_shards(ROOT)
    selectors = load('selector-hardware.json')
    kernels = load('selector-hardware-kernel-shards.json')
    failure = load('selector-hardware-kernels.json')
    figures(selectors,kernels)
    text = report(selectors,kernels,failure)
    for before,after in [('uses10/16/20','uses 10/16/20'),('compile to1,277','compile to 1,277'),
                         ('to1,739','to 1,739'),('The20-candidate','The 20-candidate'),('is8,566','is 8,566'),
                         ('each,512','each, 512'),('shots;11','shots; 11'),('use20','use 20'),
                         ('At16','At 16'),('At20','At 20'),('for190','for 190'),('and76','and 76'),
                         ('to[0,1]','to [0,1]'),('is128','is 128'),('two1,332','two 1,332'),
                         ('usage()`0','usage()` 0'),('charge2','charge 2'),('ten268','ten 268'),
                         ('capped20','capped 20'),('used75','used 75'),('give4,845','give 4,845')]:
        text = text.replace(before,after)
    (ROOT/'docs/SELECTOR_HARDWARE.md').write_text(text)
    print('Rendered report and figure from verified saved counts/predictions; no new experiments.')
