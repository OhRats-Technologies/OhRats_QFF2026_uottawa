import argparse,hashlib,json
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser(description='Export measured selector/predictor outcome evidence and chart')
parser.add_argument('--study',type=Path,default=Path('.cache/wildfire/experiments/0a0f08f2f7b7062ce698'))
parser.add_argument('--name',default='operational-pilot-screen')
parser.add_argument('--title',default='Ontario recorded-fire size pilot · chronological validation within 2010–2018')
args=parser.parse_args()
base=args.study
summary=dict(stage='exploratory_screen',final_test_sealed=True,evidence=[])
fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
for axis,subplot in zip(['selection','prediction'],axes):
 rpath=next(p for p in base.glob('*-outcome.json') if json.loads(p.read_text())['axis']==axis)
 r=json.loads(rpath.read_text());assert r['status']=='complete'
 grouped=defaultdict(list)
 for row in r['rows']:
  label=row.get('selector') if axis=='selection' and row.get('selector')!='fixed_control' else row['predictor']
  grouped[label].append(row)
 section=dict(axis=axis,outcome_sha256=hashlib.sha256(rpath.read_bytes()).hexdigest(),attempt=r['id'],seconds=r['seconds'],quality_checks=r['quality_checks'],models=[])
 for name,rows in grouped.items():
  folds=defaultdict(list)
  for row in rows:folds[str(row['fold'])].append(row['metric']['average_precision'])
  section['models'].append(dict(name=name,mean_average_precision=float(np.mean([x['metric']['average_precision'] for x in rows])),mean_roc_auc=float(np.mean([x['metric']['roc_auc'] for x in rows])),fold_average_precision={k:float(np.mean(v)) for k,v in folds.items()},mean_prevalence=float(np.mean([x['metric']['prevalence'] for x in rows])),features_by_run=[x['features'] for x in rows]))
 section['models'].sort(key=lambda x:x['mean_average_precision'])
 summary['evidence'].append(section)
 models=section['models'];labels=[m['name'].replace('_',' ') for m in models]
 subplot.barh(labels,[m['mean_average_precision'] for m in models],height=.55,color=['#a5b0b8' if not any(w in m['name'] for w in ['qaoa','qiskit']) else '#b45135' for m in models])
 for i,m in enumerate(models):subplot.scatter(list(m['fold_average_precision'].values()),[i]*3,s=14,color='#263340',zorder=3)
 subplot.set(xlabel='Average precision',title='Feature selection · fixed logistic' if axis=='selection' else 'Prediction · same 4 inputs / row caps',xlim=(0,.7))
 subplot.spines[['top','right','left']].set_visible(False);subplot.tick_params(axis='y',length=0);subplot.grid(axis='x',alpha=.15);subplot.set_axisbelow(True)
fig.suptitle(args.title,fontsize=12)

Path('docs/figures').mkdir(exist_ok=True)
fig.savefig('docs/figures/'+args.name+'.png',dpi=170,bbox_inches='tight')
Path('docs/results').mkdir(exist_ok=True)
for section in summary['evidence']:
 for model in section['models']:
  inputs=model.pop('features_by_run')
  model['feature_selection_counts']={c:sum(c in x for x in inputs) for c in sorted({c for x in inputs for c in x})}
lines=['{','  \"stage\": \"exploratory_screen\",','  \"final_test_sealed\": true,','  \"evidence\": [']
for i,section in enumerate(summary['evidence']):
 models=section.pop('models');head=json.dumps(section,separators=(',',':'))[:-1]
 lines.append('    '+head+',\"models\":[')
 lines.extend('      '+json.dumps(m,separators=(',',':'))+(',' if j<len(models)-1 else '') for j,m in enumerate(models))
 lines.append('    ]}'+(',' if i<len(summary['evidence'])-1 else ''))
lines.extend(['  ]','}']);Path('docs/results/'+args.name+'.json').write_text('\n'.join(lines)+'\n')
