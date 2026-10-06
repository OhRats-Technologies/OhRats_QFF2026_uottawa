"""Actual sampled SQD, readout diagnostics and fixed predictions; no invented samples."""
import json
import numpy as np
import pandas as pd
from wildfire_lab.selector_hardware import parent
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd
from wildfire_lab.forest_models import fit
from wildfire_lab.mitigation_hardware import write, sha
from wildfire_lab.mitigation_hardware_analysis import elapsed


def bit_rows(counts, width):
    states = np.array([int(s.replace(' ',''),2) for s in counts],dtype=np.int64)
    weights = np.array(list(counts.values()))
    bits = (states[:,None] >> np.arange(width)) & 1
    return states,bits,weights


def assignment(zero, one, width):
    _,z,wz = bit_rows(zero,width)
    _,o,wo = bit_rows(one,width)
    p01,p10 = wz@z/wz.sum(),wo@(1-o)/wo.sum()
    return np.array([[[1-a,b],[a,1-b]] for a,b in zip(p01,p10)])


def observed_readout(counts, channels, candidates):
    """Reweight only existing sampled feasible basis; do not invent SQD states."""
    n = len(channels)
    states,bits,weights = bit_rows(counts,n)
    inverse = np.array([np.linalg.pinv(a,rcond=1e-8) for a in channels])
    basis = ((np.array(candidates)[:,None] >> np.arange(n)) & 1)
    quasi = []
    for target in basis:
        factors = np.ones(len(states))
        for i in range(n):
            factors *= inverse[i,target[i],bits[:,i]]
        quasi.append(float(factors@weights/weights.sum()))
    q = np.array(quasi)
    positive = np.maximum(q,0)
    mass = positive.sum()
    return dict(basis_states=candidates,quasi_weights=q.tolist(),
                conditional_positive_weights=(positive/mass).tolist() if mass>1e-12 else None,
                signed_mass=float(q.sum()),positive_mass=float(mass),
                negative_entries=int(np.sum(q<0)),
                largest_single_channel_condition=float(max(np.linalg.cond(a) for a in channels)),
                interpretation='Approximate independent readout inversion only on actually observed feasible basis; no full distribution claim, new draws or new SQD states.')


def timings(output):
    result = {}
    for arm in ['raw','dd_twirl']:
        metrics = json.loads((output/f'{arm}_metrics.json').read_text())
        usage = float(json.loads((output/f'{arm}_usage.json').read_text()))
        charged = metrics['usage'].get('quantum_seconds',metrics['usage'].get('qpu_charge_time_seconds'))
        assert charged is not None and charged==usage
        stamps = metrics.get('timestamps',{})
        submission = json.loads((output/f'{arm}_submitted.json').read_text())
        result[arm]=dict(quantum_seconds=usage,
                        created_to_finished_seconds=elapsed(stamps,'created','finished'),
                        running_to_finished_seconds=elapsed(stamps,'running','finished'),
                        submission_roundtrip_seconds=submission['submission_roundtrip_seconds'])
    return result


def analyze(root,output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    plan = receipt['plan']
    source = parent(root,plan)
    table = pd.read_csv(root/source['intent']['plan']['dataset'])
    first,last,vfirst,vlast = plan['fold']
    train,valid = table[table.year.between(first,last)],table[table.year.between(vfirst,vlast)]
    cohorts = {len(c['features']):c for c in source['cohorts'] if c['fold']==plan['fold']}
    rows,raw_records,models = [],{},{}
    for arm in ['raw','dd_twirl']:
        counts = json.loads((output/f'{arm}_counts.json').read_text())['counts']
        assert len(counts)==18 and all(sum(c.values())==plan['selector_shots'] for c in counts)
        raw_records[arm]=counts
        for index,record in enumerate(receipt['records'][:6]):
            label = record['label']
            n,policy = label['pool_size'],label['policy']
            width = n+label['counter_qubits']
            states,bits,weights = bit_rows(counts[index],width)
            feasible = bits[:,:n].sum(axis=1)==4
            clean = feasible & (states>>n==0)
            candidate = states & ((1<<n)-1)
            saved = {}
            for state,weight in zip(candidate[feasible],weights[feasible]):
                key = str(int(state))
                saved[key]=saved.get(key,0)+int(weight)
            channels = assignment(counts[6+2*index],counts[7+2*index],width)
            cohort = cohorts[n]
            obj = {k:np.array(v) if isinstance(v,list) else v for k,v in cohort['objective'].items()}
            sector = Sector(obj)
            result = dict(arm=arm,pool_size=n,policy=policy,physical_shots=int(weights.sum()),
                          feasible_shots=int(weights[feasible].sum()),clean_counter_feasible_shots=int(weights[clean].sum()),
                          feasible_fraction=float(weights[feasible].sum()/weights.sum()),
                          clean_counter_feasible_fraction=float(weights[clean].sum()/weights.sum()),
                          observed_feasible_counts=saved,assignment=channels.tolist())
            if saved:
                sqd = diagonal_sqd(obj,dict(counts=saved))
                costs = {int(s):sector.cost[np.searchsorted(sector.states,int(s))] for s in saved}
                chosen = min(sorted(costs),key=costs.get)
                indices = [i for i in range(n) if (chosen>>i)&1]
                uniform = [sample(sector,np.repeat(1/len(sector.cost),len(sector.cost)),
                                  int(weights[feasible].sum()),137+r) for r in range(20)]
                result.update(sqd=sqd,selected_indices=indices,objective=costs[chosen],
                              gap_to_exact=float(costs[chosen]-sector.cost.min()),
                              matched_uniform_mean_gap=float(np.mean([r['gap'] for r in uniform])),
                              matched_uniform_optimum_trials=int(sum(r['optimum_found'] for r in uniform)),
                              matched_uniform_records=uniform,
                              readout=observed_readout(counts[index],channels[:n],sorted(costs)))
                columns = [cohort['features'][i] for i in indices]
                model = fit(train[columns].to_numpy(),valid[columns].to_numpy(),
                            train.mean_reported_size_ha.to_numpy(),valid.mean_reported_size_ha.to_numpy(),
                            columns,source['intent']['plan'])
                models[f'{arm}-{n}-{policy}']=model
                result['predictions']=model['rows']
            else:
                result['status']='no_feasible_hardware_sample'
            rows.append(result)
    timing = timings(output)
    result = dict(status='collected',study=plan['study'],backend=receipt['backend'],rows=rows,
                  raw_records=raw_records,models=models,timings=timing,
                  parent_evidence_sha256=plan['parent_evidence_sha256'],plan_sha256=receipt['plan_sha256'],
                  compiled_records=receipt['records'],hardware_jobs=2,physical_shots=2*18*plan['selector_shots'],
                  quantum_seconds_total=sum(r['quantum_seconds'] for r in timing.values()),
                  downstream_kernel_status='analytic reference only; separate hardware overlap stage pending',
                  final_test_accessed=False,
                  limitation='One raw/DD-twirled pair on the first reused development fold. Hardware selectors have3 counter ancillas. SQD uses only actual feasible measured states; readout reweighting invents no new sampled state. Predictors here use analytic kernels until separately measured overlaps complete.')
    write(output/'analysis.json',result)
    write(root/'docs/results/selector-hardware.json',result)
    return result
