"""Verify saved circuit counts and predictors without sampling, fitting or new states."""
import json
import numpy as np
from wildfire_lab.annual_classical import errors
from wildfire_lab.mitigation_run import digest
from wildfire_lab.mitigation_kernel import decoded
from wildfire_lab.mitigation_noise import repair_kernel, invert_readout
from wildfire_lab.selection import configurations, energies

def collect(root, output):
    manifest = json.loads((output/'manifest.json').read_text())
    for name, expected in manifest.items():
        if digest(output/name) != expected:
            raise ValueError(f'{name} evidence changed')
    data = json.loads((output/'evidence.json').read_text())
    if data['intent'] != json.loads((output/'intent.json').read_text()):
        raise ValueError('Intent mismatch')
    for path, expected in data['intent']['code_sha256'].items():
        if digest(root/path) != expected:
            raise ValueError(f'Pinned implementation changed: {path}')
    plan = data['plan']
    if digest(root/'experiments/pipeline_mitigation.json') != data['intent']['plan_sha256']:
        raise ValueError('Plan changed')
    reconstructed = {}
    count_paths = 0
    for record in data['kernels']:
        counts = np.asarray(record['counts'])
        replicas = counts.shape[1]
        assert np.all(counts.sum(axis=2)==plan['shots']//replicas)
        count_paths += counts.shape[0]*replicas
        reconstructed[(record['seed'], record['label'])] = decoded(record)[0]
        if record['label']=='raw':
            raw = reconstructed[(record['seed'], 'raw')]
            reconstructed[(record['seed'], 'raw_psd')] = repair_kernel(*raw)
            reconstructed[(record['seed'], 'raw_rank4')] = repair_kernel(*raw, rank=4)
        if record['label']=='dd_gate_measurement_twirl':
            channels = np.asarray(data['calibrations'][str(record['seed'])]['4']['channels'])
            repaired, _ = decoded(record, channels)
            reconstructed[(record['seed'], 'readout_corrected')] = repaired
            reconstructed[(record['seed'], 'readout_psd')] = repair_kernel(*repaired)
            reconstructed[(record['seed'], 'readout_rank4')] = repair_kernel(*repaired, rank=4)
    for seed in plan['seeds']:
        for n in [4, 10]:
            calibration = data['calibrations'][str(seed)][str(n)]
            counts = np.asarray(calibration['counts'])
            assert np.all(counts.sum(axis=1)==plan['calibration_shots'])
            bits = (np.arange(2**n)[:, None]>>np.arange(n))&1
            p01, p10 = counts[0]@bits/plan['calibration_shots'], counts[1]@(1-bits)/plan['calibration_shots']
            expected = [[[1-a,b],[a,1-b]] for a,b in zip(p01,p10)]
            np.testing.assert_allclose(expected, calibration['channels'])
            count_paths += 2
    raw_draws = {}
    for record in data['selectors']:
        counts = np.asarray(record['counts'])
        assert np.all(counts.sum(axis=1)==plan['shots']//len(counts))
        count_paths += len(counts)
        raw_draws[(record['seed'], record['label'])] = np.repeat(np.arange(1024), counts.sum(axis=0))
        if 'corrected_quasi' in record:
            channels = np.asarray(data['calibrations'][str(record['seed'])]['10']['channels'])
            corrected = [invert_readout(c, channels, (frame,))[0]
                         for c,frame in zip(counts,record['frames'],strict=True)]
            np.testing.assert_allclose(np.mean(corrected,axis=0), record['corrected_quasi'])
            raw_draws[(record['seed'], 'readout_corrected')] = record['reconstructed_draws']
    x = np.asarray(data['scaled_cross'])
    actual = np.asarray(data['actual_ha'])
    obj = data['selector_resources']['objective']
    obj = {k:np.asarray(v) if isinstance(v,list) else v for k,v in obj.items()}
    bits = configurations(10)
    checked = 0
    for row in data['predictions']:
        if row['kind']=='kernel':
            gram, cross = np.asarray(row['gram']), np.asarray(row['cross'])
            key = row['seed'], row['label']
            if key in reconstructed:
                np.testing.assert_allclose(gram, reconstructed[key][0], atol=1e-10)
                np.testing.assert_allclose(cross, reconstructed[key][1], atol=1e-10)
            latent = cross[:,row['support']]@np.asarray(row['dual'])+row['intercept']
        elif row['kind']=='selector':
            draws = np.asarray(row['draws'])
            key = row['seed'],row['label']
            if key in raw_draws:
                np.testing.assert_array_equal(draws,raw_draws[key])
            feasible = np.unique(draws[bits[draws].sum(axis=1)==4])
            assert np.isclose(row['feasible_fraction'], np.mean(bits[draws].sum(axis=1)==4))
            if not len(feasible):
                assert row['status']=='no_feasible_sample'
                continue
            costs = energies(obj,bits[feasible])
            best = feasible[np.argmin(costs)]
            assert row['selected_subset']==np.flatnonzero(bits[best]).tolist()
            assert np.isclose(row['sqd_energy'],costs.min())
            latent = x[:,row['selected_subset']]@np.asarray(row['coef'])+row['intercept']
        else:
            continue
        prediction = np.maximum(0, np.expm1(latent*data['y_scale']+data['y_mean']))
        np.testing.assert_allclose(prediction,row['predicted_ha'],atol=1e-8)
        for key,value in errors(actual,prediction).items():
            assert np.isclose(value,row[key])
        checked += 1
    return dict(prediction_records_checked=checked, measured_count_paths_checked=count_paths,
                new_quantum_states=0, predictor_fits=0, hardware_jobs_submitted=0,
                evidence_sha256=manifest['evidence.json'])
