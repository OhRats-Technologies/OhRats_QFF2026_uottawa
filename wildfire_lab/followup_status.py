"""Read-only status of explicitly scoped local studies, excluding private results."""
import json
from collections import Counter

PATTERNS=('library-followup*','quantum-landmarks*','kernel-convergence*','kernel-ridge*','seasonal-baseline*','shot-feasibility*','constrained-selection*','local-geometry*','tangent-prediction*','landmark-shot-ridge*','proxy-alignment*','policy-evolution-*')


def summarize(cache):
    records=[]
    for directory in sorted({p for pattern in PATTERNS for p in cache.glob(pattern) if p.is_dir()}):
        intent,outcome=directory/'intent.json',directory/'outcome.json'
        if not intent.exists() and not outcome.exists():continue
        row=dict(namespace=directory.name,intent_present=intent.exists())
        if not outcome.exists():row['saved_status']='intent_without_outcome'
        else:
            try:
                saved=json.loads(outcome.read_text())
                row.update(saved_status=saved['status'],completed_seed_records=len(saved.get('seeds',[])),
                    observed_runner_seconds=saved.get('seconds'))
                if 'conditions' in saved:row['completed_condition_records']=len(saved['conditions'])
            except (OSError,json.JSONDecodeError,KeyError,TypeError):row['saved_status']='unreadable'
        records.append(row)
    return dict(record_count=len(records),by_saved_status=dict(Counter(r['saved_status'] for r in records)),
        records=records,runtime_verified=False,
        note='Saved outcomes only. Retained repair attempts are not replications; a running record is not a live execution check.')
