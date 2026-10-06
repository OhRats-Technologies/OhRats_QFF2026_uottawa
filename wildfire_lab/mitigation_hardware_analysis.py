"""Sanitize IBM counts, verify usage and fit the frozen diagnostic regressors."""
from datetime import datetime
import json
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from wildfire_lab.annual_classical import inverse,errors
from wildfire_lab.mitigation_kernel import assemble,fit,geometry
from wildfire_lab.mitigation_noise import invert_readout,repair_kernel
from wildfire_lab.mitigation_hardware import write,sha
from wildfire_lab.sqd_selection import sampled_subspace

def dense(counts,n):
    result=np.zeros(2**n,dtype=int)
    for bits,count in counts.items():
        result[int(bits.replace(' ',''),2)]=count
    return result

def channels(zero,one,n):
    bits=(np.arange(2**n)[:,None]>>np.arange(n))&1
    p01=zero@bits/zero.sum()
    p10=one@(1-bits)/one.sum()
    return np.array([[[1-a,b],[a,1-b]] for a,b in zip(p01,p10)])

def elapsed(timestamps,a,b):
    if not timestamps.get(a) or not timestamps.get(b):
        return None
    return (datetime.fromisoformat(timestamps[b].replace('Z','+00:00'))-
            datetime.fromisoformat(timestamps[a].replace('Z','+00:00'))).total_seconds()

def refresh_usage(root,output,result):
    for arm in ['raw','dd_twirl']:
        metrics=json.loads((output/f'{arm}_metrics.json').read_text())
        usage=metrics.get('usage',{})
        seconds=usage.get('quantum_seconds')
        field='quantum_seconds'
        if seconds is None:
            seconds=usage.get('qpu_charge_time_seconds')
            field='qpu_charge_time_seconds'
        actual=output/f'{arm}_usage.json'
        if actual.exists() and seconds is not None:
            if float(json.loads(actual.read_text()))!=float(seconds):
                raise ValueError('Job usage differs from charge-time metric')
        result['timings'][arm].update(quantum_seconds=seconds,usage_metric=field)
    values=[row['quantum_seconds'] for row in result['timings'].values()]
    result['quantum_seconds_total']=sum(values) if all(v is not None for v in values) else None
    if result['quantum_seconds_total'] is not None and result['quantum_seconds_total']>result['configured_maximum_qpu_seconds']:
        result['budget_exceeded']=True
    write(output/'analysis.json',result)
    write(root/result.get('public_result_path','docs/results/pipeline-mitigation-ibm.json'),result)
    return result

def analyze(root,output):
    destination=output/'analysis.json'
    if destination.exists():
        return refresh_usage(root,output,json.loads(destination.read_text()))
    data=json.loads((output/'parent.json').read_text())
    receipt=json.loads((output/'prepared.json').read_text())
    if sha(output/'parent.json')!=receipt['parent_sha256']:
        raise ValueError('Parent analysis inputs changed')
    actual=np.asarray(data['actual_ha'])
    y=np.asarray(data['scaled_targets'])
    x=np.asarray(data['scaled_train'])
    cross=np.asarray(data['scaled_cross'])
    scaler=StandardScaler()
    scaler.mean_=np.array([data['y_mean']])
    scaler.scale_=np.array([data['y_scale']])
    scaler.n_features_in_=1
    ideal=next(r for r in data['predictions'] if r['label']=='ideal_fidelity')
    reference=np.asarray(ideal['gram'])
    obj={k:np.asarray(v) if isinstance(v,list) else v
         for k,v in data['selector_resources']['objective'].items()}
    rows,records,timings=[],{},{}
    rng=np.random.default_rng(139)
    for arm in ['raw','dd_twirl']:
        payload=json.loads((output/f'{arm}_counts.json').read_text())
        counts=payload['counts']
        vectors=[dense(c,4) for c in counts[:68]]
        selection=dense(counts[68],10)
        calibration=[dense(c,n) for c,n in zip(counts[69:],[4,4,10,10],strict=True)]
        if len(vectors)!=68 or any(c.sum()!=512 for c in vectors+calibration+[selection]):
            raise ValueError('Unexpected hardware shots')
        four=channels(*calibration[:2],4)
        ten=channels(*calibration[2:],10)
        gram,test=assemble([c[0]/512 for c in vectors],8,4)
        repaired=[invert_readout(c,four) for c in vectors]
        corrected=assemble([p[0] for p,_ in repaired],8,4)
        arms=[(arm,(gram,test)),(arm+'_psd',repair_kernel(gram,test)),
              (arm+'_rank4',repair_kernel(gram,test,rank=4)),
              (arm+'_readout',corrected),
              (arm+'_readout_psd',repair_kernel(*corrected)),
              (arm+'_readout_rank4',repair_kernel(*corrected,rank=4))]
        for name,(train_kernel,cross_kernel) in arms:
            row=fit(train_kernel,cross_kernel,y,scaler,actual,name,None)
            row.update(geometry(train_kernel,reference,y),
                train_kernel_rmse=float(np.mean((train_kernel-reference)**2)**.5),
                cross_kernel_rmse=float(np.mean((cross_kernel-np.asarray(ideal['cross']))**2)**.5))
            rows.append(row)
        quasi,diagnostic=invert_readout(selection,ten)
        weights=np.maximum(0,quasi)
        weights/=weights.sum()
        draws=np.repeat(np.arange(1024),selection)
        reconstructed=rng.choice(1024,size=512,p=weights)
        for name,selected in [(arm,draws),(arm+'_readout',reconstructed)]:
            result=sampled_subspace(obj,selected)
            bits=(selected[:,None]>>np.arange(10))&1
            result.update(kind='selector',label=name,feasible_fraction=float(np.mean(bits.sum(axis=1)==4)))
            if result['status']=='complete':
                indices=result['selected_subset']
                model=Ridge(alpha=1.).fit(x[:,indices],y)
                prediction=inverse(model.predict(cross[:,indices]),scaler)
                result.update(coef=model.coef_.tolist(),intercept=float(model.intercept_),
                              predicted_ha=prediction.tolist(),**errors(actual,prediction))
            rows.append(result)
        records[arm]=dict(kernel_counts=[c.tolist() for c in vectors],
            selector_counts=selection.tolist(),calibration_counts=[c.tolist() for c in calibration],
            four_assignment=four.tolist(),ten_assignment=ten.tolist(),
            kernel_readout_diagnostics=[d for _,d in repaired],
            selector_readout_diagnostic=diagnostic,selector_corrected_quasi=quasi.tolist(),
            selector_reconstructed_draws=reconstructed.tolist())
        metrics=json.loads((output/f'{arm}_metrics.json').read_text())
        submission=json.loads((output/f'{arm}_submitted.json').read_text())
        stamps=metrics.get('timestamps',{})
        timings[arm]=dict(quantum_seconds=metrics.get('usage',{}).get('quantum_seconds'),
            timestamps={k:stamps.get(k) for k in ['created','running','finished']},
            created_to_finished_seconds=elapsed(stamps,'created','finished'),
            running_to_finished_seconds=elapsed(stamps,'running','finished'),
            submission_roundtrip_seconds=submission['submission_roundtrip_seconds'])
    quantum=[t['quantum_seconds'] for t in timings.values()]
    result=dict(study=receipt['plan']['study'],backend=receipt['backend'],status='collected',
        public_result_path=receipt['plan'].get('public_result_path','docs/results/pipeline-mitigation-ibm.json'),
        parent_evidence_sha256=receipt['parent_sha256'],plan_sha256=receipt['plan_sha256'],
        compilation={key:receipt.get(key) for key in ['num_qubits','native_basis',
            'qsvr_physical_qubits','selector_physical_qubits','compiled_resources']},
        rows=rows,raw_records=records,timings=timings,
        quantum_seconds_total=sum(quantum) if all(q is not None for q in quantum) else None,
        configured_maximum_qpu_seconds=receipt['plan'].get('max_total_configured_qpu_seconds',120),
        hardware_jobs=2,final_test_accessed=False,
        actual_ha=data['actual_ha'],validation_years=data['validation_years'],predictor_fits=len(rows),
        classical_control_predictions=[r for r in data['predictions'] if r['kind']=='control'],
        limitation='One raw/combined hardware acquisition pair on four previously inspected development years. Independent-qubit effective calibration is approximate under correlated errors and Runtime measurement-frame averaging. Combined arm cannot isolate DD from twirling; no advantage or logical-QEC claim.')
    return refresh_usage(root,output,result)
