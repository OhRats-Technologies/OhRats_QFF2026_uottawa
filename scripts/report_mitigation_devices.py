"""Rebuild the descriptive device comparison from published counts and fitted models."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['ibm', 'marrakesh', 'quebec']
ARMS = ['raw', 'raw_readout', 'dd_twirl', 'dd_twirl_readout']


def collect():
    rows, timing, hashes = [], [], {}
    parent = None
    total = 0
    for source in SOURCES:
        path = ROOT / f'docs/results/pipeline-mitigation-{source}.json'
        data = json.loads(path.read_text())
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        parent = parent or data['parent_evidence_sha256']
        assert data['parent_evidence_sha256'] == parent
        assert data['status'] == 'collected' and not data['final_test_accessed']
        assert data['validation_years'] == [2007, 2008, 2009, 2010]
        for record in data['raw_records'].values():
            counts = record['kernel_counts'] + [record['selector_counts']] + record['calibration_counts']
            assert len(counts) == 73 and all(sum(c) == 512 for c in counts)
        charge = sum(t['quantum_seconds'] for t in data['timings'].values())
        assert charge == data['quantum_seconds_total']
        total += charge
        for arm in ARMS:
            kernel = next(r for r in data['rows'] if r['kind'] == 'kernel' and r['label'] == arm)
            selector = next(r for r in data['rows'] if r['kind'] == 'selector' and r['label'] == arm)
            rows.append(dict(backend=data['backend'],arm=arm,
                kernel_rmse=kernel['train_kernel_rmse'],qsvr_mae_ha=kernel['mae_ha'],
                feasible_fraction=selector['feasible_fraction'],
                selector_mae_ha=selector.get('mae_ha'),subset=selector.get('selected_subset')))
        timing.append(dict(backend=data['backend'],charged_qpu_seconds=charge,arms=data['timings']))
    assert total <= 120
    result = dict(status='collected',hardware_jobs=6,physical_shots=6*73*512,
        charged_qpu_seconds=total,owner_allowance_seconds=120,
        source_hashes=hashes,rows=rows,timings=timing,final_test_accessed=False,
        limitation='One raw/combined pair per backend on reused development years. Device, account, calibration and submission time differ. Descriptive comparison; no causal hardware ranking, statistical improvement or quantum advantage.')
    (ROOT/'docs/results/pipeline-mitigation-devices.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def plot(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'sans-serif','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.spines.left':False})
    fig, axes = plt.subplots(1,3,figsize=(13.8,4.8),layout='constrained')
    colors = ['#1b5462','#86bcb3','#b36b43','#e6ba91']
    labels = ['Raw','Readout repaired','DD + twirl','DD + twirl + readout']
    names = ['ibm_fez','ibm_marrakesh','ibm_quebec']
    for ax, key, title, unit in zip(axes,
        ['kernel_rmse','qsvr_mae_ha','feasible_fraction'],
        ['Kernel distance to ideal','Prediction error','Four-feature acceptance'],
        ['Training-kernel RMSE ↓','MAE · hectares per fire ↓','Fraction with exactly four features ↑']):
        for i, arm in enumerate(ARMS):
            values = [next(r[key] for r in result['rows'] if r['backend']==n and r['arm']==arm) for n in names]
            ax.bar(np.arange(3)+(i-1.5)*.19,values,.18,color=colors[i],label=labels[i],zorder=3)
        ax.set_xticks(range(3),['Fez','Marrakesh','Quebec'])
        ax.set_title(title,loc='left',fontweight='bold',pad=15)
        ax.set_ylabel(unit)
        ax.grid(axis='y',color='#e1e7e8',zorder=0)
        ax.tick_params(axis='both',length=0)
        if key == 'feasible_fraction':
            from matplotlib.ticker import PercentFormatter
            ax.yaxis.set_major_formatter(PercentFormatter(1))
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=4,frameon=False)
    fig.supxlabel('Same circuits and 512 shots/output · 6 jobs · 75 charged QPU seconds\nOne acquisition pair per device; four reused development years. No reliable hardware ranking.',fontsize=10)
    fig.savefig(ROOT/'docs/data/mitigation-devices.png',dpi=170,facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    result = collect()
    plot(result)
    print(json.dumps({k:result[k] for k in ['hardware_jobs','physical_shots','charged_qpu_seconds']}))
