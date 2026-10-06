"""Replay measured overlap matrices and stored QSVR equations without fitting."""
import json
import numpy as np
from wildfire_lab.forest_collect import digest
from wildfire_lab.annual_classical import errors
from wildfire_lab.saved_hardware_selector import close, counts_checked
from wildfire_lab.selector_hardware_analysis import assignment


def repair(gram,cross,rank=None):
    values,vectors = np.linalg.eigh((gram+gram.T)/2)
    kept = np.flatnonzero(values > 1e-10)
    if rank is not None:
        kept = kept[-rank:]
    basis = vectors[:,kept]
    return (basis*values[kept])@basis.T, cross@basis@basis.T


def assemble(values,n,m):
    gram = np.zeros((n,n))
    cursor = 0
    for i in range(n):
        for j in range(i,n):
            gram[i,j] = gram[j,i] = values[cursor]
            cursor += 1
    return gram,np.array(values[cursor:]).reshape(m,n)


def audit(root):
    path = root/'docs/results/selector-hardware-kernels.json'
    result = json.loads(path.read_text())
    plan_path = root/'experiments/selector_kernel_hardware.json'
    plan = json.loads(plan_path.read_text())
    receipt = audit_record(root,result,plan,digest(plan_path))
    receipt['result_sha256'] = digest(path)
    return receipt


def audit_record(root,result,plan,plan_hash):
    assert result['plan_sha256'] == plan_hash
    assert result['selector_result_sha256'] == digest(root/'docs/results/selector-hardware.json')
    selector = json.loads((root/'docs/results/selector-hardware.json').read_text())
    if result['status'] == 'failed':
        assert result['job_status'] == {'raw':'ERROR','dd_twirl':'ERROR'}
        assert result['hardware_jobs'] == 2 and result['error_code'] == 1520
        assert result['returned_physical_shots'] == result['predictor_fits'] == 0
        assert result['replacement_submissions'] == 0 and result['rows'] == []
        assert result['model_keys'] == plan['model_keys']
        assert result['attempted_pubs_per_job'] == len(result['compilation']) == 1332
        assert result['attempted_physical_shots'] == 2*1332*plan['kernel_shots']
        close(result['quantum_seconds_total'],sum(t['job_usage_seconds'] for t in result['timings'].values()))
        close(result['charged_qpu_seconds_total'],sum(t['qpu_charge_seconds'] for t in result['timings'].values()))
        assert all(t['circuits_execution_time_ns'] == 0 for t in result['timings'].values())
        return dict(status='verified_terminal_failure',hardware_jobs=2,error_code=1520,
                    returned_physical_shots=0,predictor_equations=0,
                    charged_qpu_seconds=result['charged_qpu_seconds_total'],
                    new_fits=0,new_quantum_evaluations=0,new_draws=0,network_requests=0,
                    limitation='Checks the published terminal-failure accounting, not private service logs or any unreturned hardware measurements.')
    assert set(result['models']) == set(plan['model_keys'])
    assert all(model == selector['models'][key] for key,model in result['models'].items())
    checked,pubs = 0,0
    for arm in plan['arms']:
        counts = result['raw_records'][arm]
        assert len(counts) == len(plan['model_keys'])*266+2
        for count in counts:
            counts_checked(count,plan['kernel_shots'],4)
        pubs += len(counts)
        channels = assignment(counts[-2],counts[-1],4)
        close(result['diagnostics'][arm]['assignment'],channels)
        # Integer state ordering is q3 q2 q1 q0; assignment is little endian.
        full_channel = channels[3]
        for q in [2,1,0]:
            full_channel = np.kron(full_channel,channels[q])
        for key,model in result['models'].items():
            relevant = [c for r,c in zip(result['compilation'],counts,strict=True) if r.get('model_key') == key]
            assert len(relevant) == 266
            raw,corrected = [],[]
            diagnostics = result['diagnostics'][arm]['kernel_readout'][key]
            for count,info in zip(relevant,diagnostics,strict=True):
                observed = np.zeros(16)
                for state,weight in count.items():
                    observed[int(state,2)] = weight/plan['kernel_shots']
                quasi = np.linalg.solve(full_channel,observed)
                close(info['quasi_probability_zero'],quasi[0])
                close(info['negative_mass'],-quasi[quasi<0].sum())
                assert info['residual'] < 1e-7
                raw.append(observed[0])
                corrected.append(np.clip(quasi[0],0,1))
            gram,cross = assemble(raw,19,4)
            calibrated = assemble(corrected,19,4)
            variants = dict(raw=(gram,cross),psd=repair(gram,cross),rank4=repair(gram,cross,4),
                            readout=calibrated,readout_psd=repair(*calibrated),readout_rank4=repair(*calibrated,rank=4))
            for label,(train_kernel,cross_kernel) in variants.items():
                row = next(r for r in result['rows'] if (r['kernel_arm'],r['model_key'],r['label']) == (arm,key,label))
                close(row['gram'],train_kernel)
                close(row['cross'],cross_kernel)
                prediction = cross_kernel[:,row['support']]@np.array(row['dual'])+row['intercept']
                p = model['preprocessing']
                hectares = np.maximum(0,np.expm1(prediction*p['y_scale']+p['y_mean']))
                close(row['predicted_ha'],hectares)
                actual = np.array(model['rows'][0]['actual_ha'])
                for metric,value in errors(actual,hectares).items():
                    close(row[metric],value)
                close(row['train_kernel_rmse'],np.mean((train_kernel-np.array(model['quantum_gram']))**2)**.5)
                close(row['cross_kernel_rmse'],np.mean((cross_kernel-np.array(model['quantum_cross']))**2)**.5)
                close(row['minimum_eigenvalue'],np.linalg.eigvalsh((train_kernel+train_kernel.T)/2).min())
                checked += 1
    assert checked == result['predictor_fits'] == 12*len(plan['model_keys'])
    assert result['physical_shots'] == pubs*plan['kernel_shots']
    close(result['quantum_seconds_total'],sum(t['quantum_seconds'] for t in result['timings'].values()))
    return dict(status='verified',kernel_pubs=pubs,predictor_equations=checked,
                physical_shots=result['physical_shots'],charged_qpu_seconds=result['quantum_seconds_total'],
                new_fits=0,new_quantum_evaluations=0,new_draws=0,network_requests=0,
                limitation='Counts-to-matrices and saved prediction-equation replay, including declared readout/PSD/rank repair; neither new hardware nor independent validation.')


def audit_shards(root):
    path = root/'docs/results/selector-hardware-kernel-shards.json'
    result = json.loads(path.read_text())
    plan_path = root/'experiments/selector_kernel_shards.json'
    plan = json.loads(plan_path.read_text())
    original = json.loads((root/plan['parent_plan']).read_text())
    assert result['plan_sha256'] == digest(plan_path)
    assert set(result['shards']) == set(plan['model_keys'])
    receipts = {key:audit_record(root,record,dict(original,model_keys=[key]),digest(plan_path))
                for key,record in result['shards'].items()}
    assert result['hardware_jobs'] == plan['max_jobs'] == 10
    assert result['predictor_fits'] == sum(r['predictor_equations'] for r in receipts.values()) == 60
    assert result['physical_shots'] == sum(r['physical_shots'] for r in receipts.values()) == 343040
    close(result['quantum_seconds_total'],sum(r['charged_qpu_seconds'] for r in receipts.values()))
    return dict(status='verified',shards=receipts,result_sha256=digest(path),
                predictor_equations=60,physical_shots=343040,charged_qpu_seconds=result['quantum_seconds_total'],
                new_fits=0,new_quantum_evaluations=0,new_draws=0,network_requests=0)
