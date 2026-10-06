"""Fit fixed QSVR to actual larger-study IBM overlap counts and declared repairs."""
import json
import numpy as np
from sklearn.preprocessing import StandardScaler
from wildfire_lab.selector_hardware_analysis import assignment, timings
from wildfire_lab.mitigation_hardware import write, sha
from wildfire_lab.mitigation_hardware_analysis import dense
from wildfire_lab.mitigation_kernel import fit, geometry, assemble
from wildfire_lab.mitigation_noise import invert_readout, repair_kernel


def analyze(root, output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    assert sha(output/'models.json')==receipt['models_sha256']
    models = json.loads((output/'models.json').read_text())
    count_records = {arm:json.loads((output/f'{arm}_counts.json').read_text())['counts']
                     for arm in ['raw','dd_twirl']}
    rows, diagnostics = [], {}
    for arm, counts in count_records.items():
        assert len(counts)==len(receipt['records'])
        assert all(sum(c.values())==receipt['shots'] for c in counts)
        channels = assignment(counts[-2],counts[-1],4)
        diagnostics[arm]=dict(assignment=channels.tolist(),kernel_readout={})
        for key, model in models.items():
            relevant = [(r,c) for r,c in zip(receipt['records'],counts,strict=True) if r.get('model_key')==key]
            raw, corrected, repair_records = [], [], []
            for record, count in relevant:
                vector = dense(count,4)
                raw.append(float(vector[0]/receipt['shots']))
                quasi, info = invert_readout(vector,channels)
                corrected.append(float(np.clip(quasi[0],0,1)))
                repair_records.append(dict(quasi_probability_zero=float(quasi[0]),**info))
            n,m = len(model['scaled_train']),len(model['scaled_cross'])
            gram,cross = assemble(raw,n,m)
            repaired = assemble(corrected,n,m)
            variants = dict(raw=(gram,cross),psd=repair_kernel(gram,cross),
                            rank4=repair_kernel(gram,cross,rank=4),readout=repaired,
                            readout_psd=repair_kernel(*repaired),readout_rank4=repair_kernel(*repaired,rank=4))
            p = model['preprocessing']
            scaler = StandardScaler()
            scaler.mean_,scaler.scale_ = np.array([p['y_mean']]),np.array([p['y_scale']])
            scaler.n_features_in_=1
            y = np.array(model['scaled_targets'])
            actual = np.array(model['rows'][0]['actual_ha'])
            ideal = np.array(model['quantum_gram'])
            for name,(train_kernel,cross_kernel) in variants.items():
                row = fit(train_kernel,cross_kernel,y,scaler,actual,name,None)
                row.update(kernel_arm=arm,model_key=key,features=model['rows'][0]['features'],
                           train_kernel_rmse=float(np.mean((train_kernel-ideal)**2)**.5),
                           cross_kernel_rmse=float(np.mean((cross_kernel-np.array(model['quantum_cross']))**2)**.5),
                           **geometry(train_kernel,ideal,y))
                rows.append(row)
            diagnostics[arm]['kernel_readout'][key]=repair_records
    timing = timings(output)
    result = dict(status='collected',study=receipt['plan']['study'],backend=receipt['backend'],
                  plan_sha256=receipt['plan_sha256'],selector_result_sha256=receipt['plan']['selector_result_sha256'],
                  models=models,rows=rows,raw_records=count_records,diagnostics=diagnostics,
                  compilation=receipt['records'],physical_qubits=receipt['physical_qubits'],
                  timings=timing,quantum_seconds_total=sum(r['quantum_seconds'] for r in timing.values()),
                  hardware_jobs=2,physical_shots=2*len(receipt['records'])*receipt['shots'],
                  shots_per_pub=receipt['shots'],kernel_subsets=len(models),predictor_fits=len(rows),
                  final_test_accessed=False,
                  limitation='Actual compute-uncompute probabilities on hardware-selected four-feature subsets; nineteen training and four reused development years. One raw/combined acquisition pair, fixed regressors/repairs, approximate independent calibration with clipped zero probabilities. No selection from final errors or causal quantum/hardware advantage.')
    write(output/'analysis.json',result)
    write(root/'docs/results/selector-hardware-kernels.json',result)
    return result
