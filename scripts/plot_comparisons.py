"""Render the measured crossed matrix and guarded cover-component effects."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(matrix_path,confirm_path,cover_path,output):
    matrix=json.loads(matrix_path.read_text())['studies'][0]
    confirm=json.loads(confirm_path.read_text())['studies'][0]
    cover=json.loads(cover_path.read_text())['studies'][0]
    selectors=['l1_ranking','classical_qubo','qaoa_same_qubo']
    predictors=['standard_logistic','robust_tanh/rbf','robust_tanh/qiskit_ZZ']
    fig,axes=plt.subplots(1,3,figsize=(14.6,3.8),layout='constrained',gridspec_kw={'width_ratios':[1,1,1.2]})
    for subplot,study,title in zip(axes[:2],[matrix,confirm],['Screen · mean AP','Fresh sample seeds · mean AP']):
        values={m['name']:m for m in study['models']}
        grid=np.array([[values[f'{p} / {s}']['mean_average_precision'] for p in predictors] for s in selectors])
        subplot.imshow(grid,cmap='Blues',vmin=.2,vmax=.4,aspect='auto')
        for i in range(3):
            for j in range(3):subplot.text(j,i,f'{grid[i,j]:.3f}',ha='center',va='center',color='white' if grid[i,j]>.32 else '#15232f',fontsize=13)
        subplot.set_xticks(range(3),['Logistic','RBF','ZZ'])
        subplot.set_yticks(range(3),['L1','Exact QUBO','QAOA'])
        subplot.set(title=title,xlabel='Predictor')
        subplot.tick_params(length=0);subplot.spines[:].set_visible(False)
    axes[0].set_ylabel('Four-feature selector')
    right=axes[2]
    controls={m['name']:m for m in cover['models']}
    base=controls['tree / geography_season / guarded_blocks']['condition_average_precision']
    for i,(group,label,color) in enumerate([('geography_water','+ water','#a1abb1'),('geography_forest','+ forest','#426c83'),('geography_cover','+ both','#254859')]):
        row=controls[f'tree / {group} / guarded_blocks']['condition_average_precision']
        delta=np.array([row[k]-base[k] for k in base])
        right.plot([delta.min(),delta.max()],[i,i],color=color,lw=2,alpha=.5)
        right.scatter(delta,np.full(6,i),s=18,color=color,alpha=.8)
        right.scatter([delta.mean()],[i],s=75,color=color,marker='|',linewidth=3)
    right.axvline(0,color='#46545d',lw=.8)
    right.set_yticks(range(3),['+ water','+ forest','+ both'])
    right.invert_yaxis();right.set(title='Guarded tree · cover components',xlabel='AP change versus geography / season',xlim=(-.06,.105))
    right.spines[['top','right','left']].set_visible(False);right.tick_params(axis='y',length=0)
    right.grid(axis='x',alpha=.15);right.set_axisbelow(True)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    provenance=dict(matrix_attempt=matrix['attempt'],confirmation_attempt=confirm['attempt'],cover_attempt=cover['attempt'],
        summary_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [matrix_path,confirm_path,cover_path]},
        plot_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        caption='Matrices: reused chronological years; screen seeds 42/73/101, fresh seeds 211/307/401; 256 training/512 validation caps. Right: six dependent fold/direction conditions, 200 km blocks and 50 km guard. Points/ranges describe conditions, not confidence intervals. Final-test performance sealed.')
    output.with_suffix('.json').write_text(json.dumps(provenance,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',type=Path,default=Path('docs/results/historical-woodland-combinations.json'))
    parser.add_argument('--confirmation',type=Path,default=Path('docs/results/historical-woodland-combinations-confirm.json'))
    parser.add_argument('--cover',type=Path,default=Path('docs/results/historical-cover-components.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/woodland-comparisons.png'))
    args=parser.parse_args();plot(args.matrix,args.confirmation,args.cover,args.output)
