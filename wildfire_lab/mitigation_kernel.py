"""Sample actual four-qubit compute-uncompute kernels with fixed suppression arms."""
import numpy as np
from qiskit import transpile, qpy
from wildfire_lab.annual_data import digest
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.algorithms import QSVR
from sklearn.svm import SVR
from sklearn.metrics.pairwise import rbf_kernel
from wildfire_lab.library_kernel import matrices
from wildfire_lab.annual_classical import inverse, errors, gamma
from wildfire_lab.mitigation_noise import suppressed_circuit, sample, invert_readout, repair_kernel

ARMS = {
    'raw': (False, False, False),
    'dd': (True, False, False),
    'gate_twirl': (False, True, False),
    'dd_gate_twirl': (True, True, False),
    'dd_gate_measurement_twirl': (True, True, True),
}

ISOLATED = ['shot_only', 'readout_only', 'coherent_only', 'amplitude_only', 'phase_only']

def geometry(gram, ideal, y):
    symmetric = (gram+gram.T)/2
    values = np.linalg.eigvalsh(symmetric)
    positive = np.maximum(0, values)
    weights = positive/positive.sum() if positive.sum() else positive
    h = np.eye(len(y))-np.ones((len(y), len(y)))/len(y)
    centered, target = h@symmetric@h, h@np.outer(y, y)@h
    return dict(diagonal_deviation=float(np.linalg.norm(np.diag(gram)-1)),
                minimum_eigenvalue=float(values.min()),
                negative_spectral_mass=float(-values[values<0].sum()),
                effective_rank=float(np.exp(-np.sum(weights[weights>0]*np.log(weights[weights>0])))),
                exact_alignment=float(np.sum(gram*ideal)/(np.linalg.norm(gram)*np.linalg.norm(ideal))),
                target_alignment=float(np.sum(centered*target)/(np.linalg.norm(centered)*np.linalg.norm(target))),
                asymmetry=float(np.linalg.norm(gram-gram.T)))

def assemble(values, n, m):
    gram = np.zeros((n, n))
    cross = np.zeros((m, n))
    cursor = 0
    for i in range(n):
        for j in range(i, n):
            gram[i, j] = gram[j, i] = values[cursor]
            cursor += 1
    cross[:] = np.asarray(values[cursor:]).reshape(m, n)
    return gram, cross

def decoded(record, channels=None):
    values, diagnostics = [], []
    for rows, frames in zip(record['counts'], record['frames'], strict=True):
        if channels is None:
            values.append(sum(row[0] for row in rows)/record['shots'])
        else:
            corrected = [invert_readout(np.asarray(row), channels, (frame,))
                         for row, frame in zip(rows, frames, strict=True)]
            values.append(float(np.mean([p[0] for p, _ in corrected])))
            diagnostics.extend(d for _, d in corrected)
    return assemble(values, record['n'], record['m']), diagnostics

def fit(gram, cross, y, scaler, actual, label, seed):
    model = QSVR(quantum_kernel='precomputed', C=1., epsilon=.2)
    model.fit(gram, y)
    prediction = inverse(model.predict(cross), scaler)
    return dict(kind='kernel', label=label, seed=seed, gram=gram.tolist(),
                cross=cross.tolist(), support=model.support_.tolist(),
                dual=model.dual_coef_[0].tolist(), intercept=float(model.intercept_[0]),
                predicted_ha=prediction.tolist(), **errors(actual, prediction))

def experiment(x, cross, y, scaler, actual, plan, calibrations, output):
    angles = plan['angle_amplitude']*np.tanh(x/2)
    validation = plan['angle_amplitude']*np.tanh(cross/2)
    ideal, ideal_cross, resources = matrices(angles, validation, reps=1)
    rows = [fit(ideal, ideal_cross, y, scaler, actual, 'ideal_fidelity', None)]
    rbf = SVR(kernel='precomputed', C=1., epsilon=.2).fit(rbf_kernel(x, gamma=gamma(x)), y)
    prediction = inverse(rbf.predict(rbf_kernel(cross, x, gamma=gamma(x))), scaler)
    rows.append(dict(kind='control', label='classical_rbf', seed=None,
                     predicted_ha=prediction.tolist(), **errors(actual, prediction)))
    feature = zz_feature_map(4, reps=1, entanglement='linear')
    bound = [feature.assign_parameters(row) for row in angles]
    valid = [feature.assign_parameters(row) for row in validation]
    circuits = [bound[i].compose(bound[j].inverse())
                for i in range(len(x)) for j in range(i, len(x))]
    circuits += [v.compose(t.inverse()) for v in valid for t in bound]
    compiled = transpile(circuits, basis_gates=['rz', 'sx', 'x', 'cx'],
                         optimization_level=1, seed_transpiler=7)
    with (output/'kernel_base.qpy').open('wb') as stream:
        qpy.dump(compiled, stream)
    raw_records = []
    for seed in plan['seeds']:
        channels = np.asarray(calibrations[str(seed)]['4']['channels'])
        for label in ISOLATED+list(ARMS):
            dd, gate, measurement = ARMS.get(label, (False, False, False))
            noise = dict(plan['noise'])
            if label in ISOLATED:
                noise = {key: 0. for key in noise}
                fields = {'shot_only': [], 'readout_only': ['readout_0_to_1', 'readout_1_to_0'],
                          'coherent_only': ['cx_target_z_radians', 'spectator_idle_z_radians'],
                          'amplitude_only': ['amplitude_damping'], 'phase_only': ['phase_damping']}[label]
                noise.update({key: plan['noise'][key] for key in fields})
            replicas = plan['randomizations'] if gate else 1
            frames = plan['frames']['4'] if measurement else [0]*replicas
            paths = [suppressed_circuit(qc, noise, dd,
                                        seed+r if gate else None, damping=True)
                     for qc in compiled for r in range(replicas)]
            counts, probabilities = sample(paths, plan['shots']//replicas, seed,
                                          noise, frames*len(compiled), density=True)
            record = dict(seed=seed, label=label, n=len(x), m=len(cross), shots=plan['shots'],
                          counts=counts.reshape(len(compiled), replicas, 16).tolist(),
                          frames=[frames]*len(compiled),
                          logical_probabilities=probabilities.reshape(len(compiled), replicas, 16).tolist())
            raw_records.append(record)
            if label == 'shot_only':
                reference = assemble(probabilities[:, 0], len(x), len(cross))
                np.testing.assert_allclose(reference[0], ideal, atol=1e-10)
                np.testing.assert_allclose(reference[1], ideal_cross, atol=1e-10)
            arms = [(label, decoded(record)[0])]
            if label == 'raw':
                raw = arms[0][1]
                arms += [('raw_psd', repair_kernel(*raw)),
                         ('raw_rank4', repair_kernel(*raw, rank=4))]
            if measurement:
                corrected, diagnostic = decoded(record, channels)
                record['readout_diagnostics'] = diagnostic
                arms += [('readout_corrected', corrected),
                         ('readout_psd', repair_kernel(*corrected)),
                         ('readout_rank4', repair_kernel(*corrected, rank=4))]
            for name, (gram, test) in arms:
                row = fit(gram, test, y, scaler, actual, name, seed)
                row.update(train_kernel_rmse=float(np.mean((gram-ideal)**2)**.5),
                           cross_kernel_rmse=float(np.mean((test-ideal_cross)**2)**.5),
                           negative_eigenvalues=int((np.linalg.eigvalsh((gram+gram.T)/2)<-1e-10).sum()))
                row.update(geometry(gram, ideal, y))
                row['r2'] = float(1-np.sum((actual-np.asarray(row['predicted_ha']))**2)/np.sum((actual-actual.mean())**2))
                rows.append(row)
    return rows, raw_records, dict(analytic_reference=resources, pairs=len(compiled),
        base_circuits_sha256=digest(output/'kernel_base.qpy'),
        forward_circuits=len(compiled)*(len(ISOLATED)+sum(4 if arm[1] else 1 for arm in ARMS.values()))*len(plan['seeds']),
        forward_shots=len(compiled)*(len(ISOLATED)+len(ARMS))*len(plan['seeds'])*plan['shots'],
        compiled_max_cx=max(int(qc.count_ops().get('cx', 0)) for qc in compiled))
