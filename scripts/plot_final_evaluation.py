"""Plot frozen held-out performance; full and capped budgets stay separate."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(cache,summary_path,output):
    outcome=cache/'outcome.json';summary=json.loads(summary_path.read_text());record=json.loads(outcome.read_text())
    if digest(outcome)!=summary['outcome_sha256'] or digest(cache/'features.csv')!=summary['test_dataset']['data_sha256']:
        raise ValueError('Use the audited final snapshot')
    test=pd.read_csv(cache/'features.csv');full=record['rows']['full_training_models']
    fig,axes=plt.subplots(1,3,figsize=(14.5,4.4),layout='constrained',gridspec_kw={'width_ratios':[1.15,1.05,1]})
    colors=['#24664e','#77858e','#b48252']
    choices=[('tree','geography_cover','Cover tree'),('tree','geography_season','Geography tree'),('logistic','geography_cover','Cover logistic')]
    for (model,group,label),color in zip(choices,colors):
        row=next(r for r in full if r['predictor']==model and r['group']==group)
        precision,recall,_=precision_recall_curve(test.target,row['predictions'])
        axes[0].step(recall,precision,where='post',color=color,lw=1.6,label=label+' · '+f"{row['metric']['average_precision']:.3f}")
    axes[0].axhline(test.target.mean(),color='#acb4b9',lw=1,ls='--',label='Test prevalence')
    axes[0].set(title='Full training · 3,820 held-out fires',xlabel='Recall',ylabel='Precision',xlim=(0,1),ylim=(0,1))
    axes[0].legend(frameon=False,fontsize=9,loc='upper right')
    years=sorted(test.year.unique())
    for (model,group,label),color in zip(choices[:2],colors):
        row=next(r for r in full if r['predictor']==model and r['group']==group)
        ap=[row['metrics_by_year'][str(year)]['average_precision'] for year in years]
        axes[1].plot(years,ap,'o-',color=color,lw=1.6,markersize=4,label=label)
    axes[1].plot(years,[float(test.loc[test.year.eq(y),'target'].mean()) for y in years],':',color='#acb4b9',label='Prevalence')
    axes[1].set(title='Same frozen models · by year',xlabel='Test year',ylabel='Average precision',ylim=(0,.8),xticks=years)
    axes[1].legend(frameon=False,fontsize=9,loc='upper left')
    selectors=['l1_ranking','classical_qubo','qaoa_same_qubo'];predictors=['standard_logistic','robust_tanh/rbf','robust_tanh/qiskit_ZZ']
    rows=record['rows']['capped_crossed_matrix']
    grid=np.array([[np.mean([r['metric']['average_precision'] for r in rows if r['group']==s and r['predictor']==p]) for p in predictors] for s in selectors])
    axes[2].imshow(grid,cmap='Blues',vmin=.3,vmax=.45,aspect='auto')
    for i in range(3):
        for j in range(3):axes[2].text(j,i,f'{grid[i,j]:.3f}',ha='center',va='center',color='white' if grid[i,j]>.405 else '#20313d',fontsize=13)
    axes[2].set(title='Capped matrix · mean AP',xticks=range(3),xticklabels=['Logistic','RBF','ZZ'],yticks=range(3),yticklabels=['L1','Exact QUBO','QAOA'],xlabel='256 train / 512 test · three seeds')
    axes[2].tick_params(length=0);axes[2].spines[:].set_visible(False)
    for ax in axes[:2]:
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12);ax.set_axisbelow(True)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    meta=dict(outcome_sha256=digest(outcome),summary_sha256=digest(summary_path),plot_recipe_sha256=digest(Path(__file__)),figure_sha256=digest(output),
              caption='Frozen 2019–2024 test. Left/middle: 37,801 training and 3,820 test fires. Right: each selector/predictor shares 256 training labels and 512 test fires per seed (211/307/401); samples overlap. Full and capped models are different budgets. Year/seed differences are descriptive, not confidence intervals.')
    output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=Path('.cache/wildfire/final-test'))
    parser.add_argument('--summary',type=Path,default=Path('docs/results/final-evaluation.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/final-evaluation.png'))
    args=parser.parse_args();plot(args.cache,args.summary,args.output)
