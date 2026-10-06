"""Evaluate all declared repairs on measured frozen kernels; never pick a winner."""
import json
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from qiskit_machine_learning.algorithms import QSVR
from wildfire_lab.annual_classical import inverse, errors
from wildfire_lab.search_counts import timing
from wildfire_lab.selector_hardware_analysis import assignment
from wildfire_lab.mitigation_kernel import assemble, geometry
from wildfire_lab.mitigation_noise import invert_readout, repair_kernel
from wildfire_lab.mitigation_hardware import sha, write


def variants(records, channels, n, m):
    raw, corrected, diagnostics = [], [], []
    for counts in records:
        vector = np.zeros(16)
        for bits, frequency in counts.items():
            vector[int(bits.replace(' ', ''), 2)] += frequency
        raw.append(vector[0]/vector.sum())
        quasi, diagnostic = invert_readout(vector, channels)
        corrected.append(float(np.clip(quasi[0], 0, 1)))
        diagnostics.append(dict(quasi_probability_zero=float(quasi[0]), **diagnostic))
    gram, cross = assemble(raw, n, m)
    readout = assemble(corrected, n, m)
    return dict(raw=(gram, cross), psd=repair_kernel(gram, cross),
                rank4=repair_kernel(gram, cross, rank=4), readout=readout,
                readout_psd=repair_kernel(*readout),
                readout_rank4=repair_kernel(*readout, rank=4)), diagnostics


def analyze(output):
    if (output/'analysis.json').exists():
        return json.loads((output/'analysis.json').read_text())
    receipt = json.loads((output/'prepared.json').read_text())
    assert sha(output/'models.json') == receipt['models_sha256']
    models = json.loads((output/'models.json').read_text())
    rows, counts_by_arm, resources, calibrations = [], {}, {}, {}
    for job in receipt['jobs']:
        child = output/job['label']
        assert json.loads((child/'status.json').read_text())['status'] == 'DONE'
        counts = json.loads((child/'counts.json').read_text())['counts']
        assert len(counts) == len(job['records'])
        assert all(sum(c.values()) == job['shots'] for c in counts)
        counts_by_arm[job['arm']] = counts
        resources[job['arm']] = timing(child)
        channels = assignment(counts[-2], counts[-1], 4)
        calibrations[job['arm']] = dict(channels=channels.tolist(), diagnostics={})
        for panel, model in models.items():
            original = model['rows'][2]
            actual, y = np.asarray(model['actual_ha']), np.asarray(model['scaled_targets'])
            p = model['preprocessing']
            scaler = StandardScaler()
            scaler.mean_, scaler.scale_ = np.array([p['y_mean']]), np.array([p['y_scale']])
            scaler.n_features_in_ = 1
            measured = [c for r, c in zip(job['records'], counts, strict=True) if r.get('model') == panel]
            kernels, diagnostics = variants(measured, channels, len(original['scaled_train']),
                                           len(original['scaled_cross']))
            calibrations[job['arm']]['diagnostics'][panel] = diagnostics
            specification = original['specification']
            for repair, (gram, cross) in kernels.items():
                fitted = QSVR(quantum_kernel='precomputed', C=specification['C'],
                              epsilon=specification['epsilon']).fit(gram, y)
                scaled = fitted.predict(cross)
                prediction = inverse(scaled, scaler)
                row = dict(panel=panel, arm=job['arm'], repair=repair,
                    specification=specification, columns=original['columns'],
                    train_matrix=gram.tolist(), cross_matrix=cross.tolist(),
                    predicted_scaled=scaled.tolist(), predicted_ha=prediction.tolist(),
                    actual_ha=actual.tolist(), parameters=dict(intercept=float(fitted.intercept_[0]),
                        support=fitted.support_.tolist(), dual_coef=fitted.dual_coef_[0].tolist()),
                    train_kernel_rmse=float(np.mean((gram-np.asarray(original['train_matrix']))**2)**.5),
                    cross_kernel_rmse=float(np.mean((cross-np.asarray(original['cross_matrix']))**2)**.5),
                    **errors(actual, prediction), **geometry(gram, np.asarray(original['train_matrix']), y))
                rows.append(row)
    result = dict(study=receipt['plan']['study'], backend=receipt['plan']['backend'],
        plan_sha256=receipt['plan_sha256'], models=models, rows=rows,
        physical_counts=counts_by_arm, compilation=receipt['jobs'][0]['records'],
        physical_qubits=receipt['physical_qubits'], calibrations=calibrations,
        resources=resources, physical_shots=sum(sum(c.values()) for arm in counts_by_arm.values() for c in arm),
        hardware_jobs=len(resources), charged_seconds=sum(r['charged_seconds'] for r in resources.values()),
        predictor_fits=len(rows), final_test_accessed=False, code_sha256=sha(Path(__file__)),
        limitation='Measured tuned kernels, fixed before acquisition, with all six declared repairs. No repair promotion or parameter retuning on validation. Hardware subset inner tuning is conditional on full outer-training selection; MI reference refits inner selection. One raw/combined pair, approximate independent readout inversion, clipped probabilities and PSD/rank projection. No logical QEC, replicated-device ranking or independent climate test.')
    write(output/'analysis.json', result)
    return result
