"""Replay fixed policies over existing compatible training-period candidate panels."""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wildfire_lab.discovery_replay import replay
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/encoding-replay.json')
    args=parser.parse_args()
    config=json.loads((ROOT/'experiments/qiskit_library_followup.json').read_text())['replay']
    source=next((ROOT/'.cache/wildfire/experiments').glob('*/'+config['attempt']+'-outcome.json'))
    outcome=json.loads(source.read_text());assert outcome['status']=='complete'
    worlds=defaultdict(dict)
    for row in outcome['rows']:
        assert row['fold'][-1]<=2018 and row['train_rows']==256 and row['validation_rows']==512
        key=(tuple(row['fold']),row['seed'])
        worlds[key][row['predictor']]=dict(ap=row['metric']['average_precision'],
            seconds=row['fit_seconds']+row.get('kernel_seconds',0)+row.get('preprocess_seconds',0))
    rows=[]
    for (fold,seed),panel in sorted(worlds.items()):
        for policy in config['policies']:
            rows.append(dict(fold=list(fold),seed=seed,**replay(panel,policy,config['budget'])))
    development=[r for r in rows if r['fold'][-1]<=2014]
    means={p:sum(r['best_ap'] for r in development if r['policy']==p)/6 for p in config['policies']}
    calls={p:sum(r['evaluations'] for r in development if r['policy']==p)/6 for p in config['policies']}
    chosen=max(config['policies'],key=lambda p:(means[p],-calls[p]))
    result=dict(status='complete_historical_replay',source_attempt=config['attempt'],
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        code_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                     ['wildfire_lab/discovery_replay.py','scripts/replay_encoding_history.py']},
        development_mean_best_ap=means,development_mean_calls=calls,selected_policy=chosen,
        later_fold=[r for r in rows if r['policy']==chosen and r['fold'][-1]==2018],
        rows=rows,online_model_evaluations=0,
        limitations='Reveals actual stored rows only. Finite matched panel, not original discovery-tree ancestry. All panels were previously inspected; later-fold replay is not independent policy validation. Component times are recorded proxies, not new isolated runtime benchmarks.')
    args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(policy=chosen,development=means,calls=calls)))


if __name__=='__main__':main()
