"""Draw descriptive forest/selector comparisons from published, audited results."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/'docs/results'/f'{name}.json').read_text())


def style():
    plt.rcParams.update({'font.size':10,'font.family':'sans-serif','axes.spines.top':False,
                         'axes.spines.right':False,'axes.spines.left':False,
                         'axes.titleweight':'bold','axes.titlelocation':'left'})


def forest():
    p, o = load('forest-expansion'), load('forest-order-controls')
    table = pd.DataFrame(p['aggregate']+o['aggregate']).set_index(['condition','model'])
    conditions = ['weather','weather_structure','interleaved8','interleaved_zero8','interleaved_calendar8']
    labels = ['Weather\n4 inputs','Forest added\n8 grouped inputs','Same forest\n8 interleaved','Zero control\n8 interleaved','Date control\n8 interleaved']
    fig,ax = plt.subplots(figsize=(12.5,5.7),layout='constrained')
    for i,(model,color) in enumerate([('ridge','#87b8b0'),('rbf','#315f6a'),('qsvr','#bc714e')]):
        values = [table.loc[(c,model),'mae_ha'] for c in conditions]
        bars = ax.bar(np.arange(len(conditions))+(i-1)*.23,values,.22,color=color,label=model.upper(),zorder=3)
        ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    ax.axhline(92.,color='#829094',ls='--',lw=1,label='Training-mean reference · 92.0')
    ax.set_xticks(range(len(conditions)),labels)
    ax.set_ylim(0,110)
    ax.set_ylabel('Mean development MAE · hectares per reported fire ↓')
    ax.set_title('Forest inputs help these fixed development models; input order changes QSVR',pad=16)
    ax.grid(axis='y',color='#e6ebec',zorder=0)
    ax.tick_params(length=0)
    fig.legend(*ax.get_legend_handles_labels(),loc='outside upper center',ncol=4,frameon=False)
    fig.supxlabel('Three reused chronological folds ending 2010 / 2014 / 2018. Placeholder controls are post-hoc.\nReconstructed forest imagery prevents an as-of forecast claim; original final scores are unchanged.',fontsize=10)
    fig.savefig(ROOT/'docs/figures/forest-expansion.png',dpi=160,facecolor='white')
    plt.close(fig)


def selectors():
    result = load('selector-scaling')
    sampling = pd.DataFrame(result['sampling'])
    scores = pd.DataFrame(result['aggregate'])
    colors = dict(uniform='#54666c',fixed='#adbab7',optimized1='#83bdb3',optimized2='#bd704b',exact='#405880',mi='#80638f')
    labels = dict(uniform='Uniform',fixed='Fixed p=1',optimized1='Optimized p=1',optimized2='Optimized p=2',exact='Exact objective',mi='MI ranking')
    fig,axes = plt.subplots(1,3,figsize=(14.5,5.4),layout='constrained')
    for name in ['uniform','fixed','optimized1','optimized2']:
        rows = sampling[(sampling.policy==name)&(sampling.shots==1024)].sort_values('pool_size')
        for ax,key in zip(axes[:2],['mean_gap','optimum_wins']):
            values = rows[key] if key=='mean_gap' else rows.optimum_wins/rows.trials
            ax.plot(rows.pool_size,values,'o-',color=colors[name],label=labels[name],lw=2)
    for name in ['uniform','optimized1','optimized2','exact','mi']:
        rows = scores[(scores.selector==name)&(scores.model=='qsvr')].sort_values('pool_size')
        axes[2].plot(rows.pool_size,rows.mae_ha,'o-',color=colors[name],label=labels[name],lw=2)
    for ax,title,ylabel in zip(axes,['Objective gap ↓','Exact-objective hits ↑','Prediction error ↓'],
                               ['Mean sampled gap to exhaustive minimum','Fraction of 60 sampling trials','QSVR MAE · hectares per fire']):
        ax.set_title(title,pad=15)
        ax.set_ylabel(ylabel)
        ax.set_xticks([10,16,20])
        ax.set_xlabel('Candidate features / logical selector qubits')
        ax.grid(axis='y',color='#e6ebec')
        ax.tick_params(length=0)
    from matplotlib.ticker import PercentFormatter
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[2].legend(frameon=False,fontsize=8,loc='upper left')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=4,frameon=False)
    fig.supxlabel('1,024 classical sector draws per trial · k=4 · 20 Monte Carlo seeds × 3 reused development folds\nPrediction uses one declared sample seed per fold; objective success is not predictive success or quantum advantage.',fontsize=10)
    fig.savefig(ROOT/'docs/figures/selector-scaling.png',dpi=160,facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    style()
    forest()
    selectors()
