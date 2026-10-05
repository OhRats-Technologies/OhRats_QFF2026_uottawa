"""Reconstruct frozen selector probabilities, sampled choices and predictions."""
import math
import numpy as np
from qiskit import transpile
from qiskit.quantum_info import Statevector
from wildfire_lab.selection import configurations,energies,fit_objective,exact_subset
from wildfire_lab.constrained_qaoa import circuit
from wildfire_lab.constrained_selection import sampled
from wildfire_lab.evaluation import scores


def close(a,b):np.testing.assert_allclose(a,b,atol=1e-9,rtol=1e-9)


def validate_seed(train,valid,parent,plan,record):
    train,valid,hashes=sampled(train,valid,parent,record['seed']);assert all(record[k]==v for k,v in hashes.items())
    assert (record['train_rows'],record['validation_rows'])==(len(train),len(valid))
    assert (record['train_positive'],record['validation_positive'])==(int(train.target.sum()),int(valid.target.sum()))
    columns=plan['features'];p=record['preprocessing'];raw=train[columns].to_numpy(dtype=float)
    median=np.nan_to_num(np.nanmedian(raw,axis=0),nan=0);x=np.where(np.isnan(raw),median,raw)
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    for name,value in [('median',median),('mean',mean),('scale',scale)]:close(p[name],value)
    x=(x-mean)/scale;v=valid[columns].to_numpy(dtype=float);v=(np.where(np.isnan(v),median,v)-mean)/scale
    objective=fit_objective(x,train.target.to_numpy(),plan['feature_count'],record['seed'])
    for key,value in objective.items():close(record['objective'][key],value)
    bits=configurations(len(columns));cost=energies(objective,bits);mask=bits.sum(axis=1)==plan['feature_count']
    exact,minimum=exact_subset(objective);close(record['exact_objective'],minimum)
    choices={'exact':exact};seen=set();calls=0
    for q in record['quantum']:
        key=(q['initial'],q['mixer']);assert key not in seen;seen.add(key)
        qc=circuit(objective,q['parameters'],*key);probability=Statevector.from_instruction(qc).probabilities()
        close(q['probabilities'],probability);close(q['feasible_probability'],probability[mask].sum())
        close(q['expected_objective'],probability@cost)
        if key==('feasible','XY'):assert abs(probability[mask].sum()-1)<=plan['mechanism_tolerance']
        if key==('all','XY'):assert abs(probability[mask].sum()-math.comb(len(columns),plan['feature_count'])/len(bits))<=plan['mechanism_tolerance']
        rng=np.random.default_rng(record['seed']);close(q['initial_parameters'],rng.uniform(0,.5,2))
        draws=rng.choice(len(bits),size=plan['shots'],p=np.asarray(q['probabilities']));np.testing.assert_array_equal(q['draws'],draws)
        eligible=draws[mask[draws]];assert q['feasible_draws']==len(eligible)
        chosen=int(eligible[np.argmin(cost[eligible])]) if len(eligible) else None
        assert q['selected_state']==chosen
        indices=np.flatnonzero(bits[chosen]).tolist() if chosen is not None else None
        assert q['selected_indices']==indices;choices['/'.join(key)]=indices
        if chosen is None:assert q['selected_objective'] is None
        else:close(q['selected_objective'],cost[chosen])
        assert 0<q['objective_calls']<=plan['max_objective_calls'] and q['quantum_state_evaluations']==q['objective_calls']+1
        calls+=q['quantum_state_evaluations']
        compiled=transpile(qc,basis_gates=plan['logical_gate_basis'],optimization_level=plan['transpiler_optimization_level'],seed_transpiler=record['seed'])
        assert dict(compiled.count_ops())==q['logical_gate_counts'] and compiled.depth()==q['logical_depth']
    assert seen=={(a,b) for a in plan['initial_states'] for b in plan['mixers']}
    rows={row['selector']:row for row in record['rows']};assert len(rows)==len(record['rows'])
    assert set(rows)==set(plan['classical_controls'])|{'/'.join(q) for q in seen}
    l1=rows['l1'];choices['l1']=np.argsort(-np.abs(l1['l1_coefficient']),kind='stable')[:plan['feature_count']].tolist()
    assert 0<=l1['l1_iterations']<plan['l1']['max_iter']
    for name in ['uniform_all','uniform_feasible']:
        rng=np.random.default_rng(record['seed']);draws=rng.choice(len(bits) if name=='uniform_all' else np.flatnonzero(mask),size=plan['shots'])
        np.testing.assert_array_equal(rows[name]['draws'],draws);eligible=draws[mask[draws]];assert rows[name]['feasible_draws']==len(eligible)
        chosen=int(eligible[np.argmin(cost[eligible])]) if len(eligible) else None
        choices[name]=np.flatnonzero(bits[chosen]).tolist() if chosen is not None else None
    fits=0
    for name,row in rows.items():
        indices=choices[name]
        if indices is None:assert row['status']=='no_feasible_draw';continue
        assert row['status']=='complete' and row['indices']==indices and row['features']==[columns[i] for i in indices]
        assert len(set(indices))==plan['feature_count'];b=np.zeros(len(columns));b[indices]=1
        value=energies(objective,b[None,:])[0];close(row['selected_objective'],value);close(row['objective_gap'],value-minimum)
        prediction=v[:,indices]@row['coefficient']+row['intercept'];close(row['predictions'],prediction)
        actual=scores(valid.target.to_numpy(),prediction,False)
        for key,value in actual.items():close(row['metric'][key],value)
        assert 0<=row['iterations']<plan['logistic']['max_iter'];fits+=1
    return dict(quantum_state_evaluations=calls,predictor_fits=fits,audit_reconstruction_states=len(seen))


def review(records):
    result={}
    for group in sorted({r['group'] for r in records}):
        seeds=[r for r in records if r['group']==group];selectors=sorted({r['selector'] for s in seeds for r in s['rows']})
        result[group]={}
        for name in selectors:
            rows=[r for s in seeds for r in s['rows'] if r['selector']==name and r['status']=='complete']
            quantum=[q for s in seeds for q in s['quantum'] if q['initial']+'/'+q['mixer']==name]
            result[group][name]=dict(completed_samples=len(rows),mean_ap=float(np.mean([r['metric']['average_precision'] for r in rows])) if rows else None,
                mean_objective_gap=float(np.mean([r['objective_gap'] for r in rows])) if rows else None,
                quantum_mean_feasible_probability=float(np.mean([q['feasible_probability'] for q in quantum])) if quantum else None,
                quantum_optimizer_successes=sum(q['optimizer_success'] for q in quantum) if quantum else None)
    return result
