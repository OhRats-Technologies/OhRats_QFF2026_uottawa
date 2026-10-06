"""Fixed annual QUBO circuits, sampled SQD and matched classical controls."""
import numpy as np
from qiskit import transpile, qpy
from wildfire_lab.annual_data import digest
from sklearn.linear_model import Ridge
from wildfire_lab.annual_selectors import objective
from wildfire_lab.constrained_qaoa import circuit
from wildfire_lab.sqd_selection import sampled_subspace
from wildfire_lab.selection import configurations, energies, exact_subset
from wildfire_lab.annual_classical import inverse, errors
from wildfire_lab.mitigation_noise import suppressed_circuit, sample, invert_readout
from wildfire_lab.mitigation_kernel import ARMS

def evaluate(obj, draws, x, cross, y, scaler, actual, label, seed):
    result = sampled_subspace(obj, draws)
    bits = configurations(x.shape[1])
    result.update(kind='selector', label=label, seed=seed, draws=draws.tolist(),
                  feasible_fraction=float(np.mean(bits[draws].sum(axis=1)==obj['k'])))
    if result['status'] == 'complete':
        indices = result['selected_subset']
        model = Ridge(alpha=1.).fit(x[:, indices], y)
        prediction = inverse(model.predict(cross[:, indices]), scaler)
        result.update(coef=model.coef_.tolist(), intercept=float(model.intercept_),
                      predicted_ha=prediction.tolist(), **errors(actual, prediction))
    return result

def experiment(x, cross, y, scaler, actual, plan, calibrations, output):
    obj = objective(x, y, dict(selected_count=4, cardinality_penalty=2.,
                              redundancy_weight=.5, relevance_neighbors=3), 7)
    qc = transpile(circuit(obj, [.4, .2], initial='feasible', mixer='XY'),
                   basis_gates=['rz', 'sx', 'x', 'cx'], optimization_level=1, seed_transpiler=7)
    with (output/'selector_base.qpy').open('wb') as stream:
        qpy.dump(qc, stream)
    bits = configurations(10)
    feasible = np.flatnonzero(bits.sum(axis=1)==4)
    exact, optimum = exact_subset(obj)
    rows, records = [], []
    for seed in plan['seeds']:
        rng = np.random.default_rng(seed)
        controls = {
            'uniform_all': rng.integers(1024, size=plan['shots']),
            'uniform_feasible': rng.choice(feasible, size=plan['shots']),
            'exact_210': np.array([int(sum(1<<i for i in exact))]),
        }
        for label, draws in controls.items():
            rows.append(evaluate(obj, draws, x, cross, y, scaler, actual, label, seed))
        for label in ['ideal']+list(ARMS):
            dd, gate, measurement = ARMS.get(label, (False, False, False))
            replicas = plan['randomizations'] if gate else 1
            frames = plan['frames']['10'] if measurement else [0]*replicas
            paths = [qc if label=='ideal' else suppressed_circuit(
                qc, plan['noise'], dd, seed+r if gate else None) for r in range(replicas)]
            counts, probabilities = sample(paths, plan['shots']//replicas, seed,
                                          None if label=='ideal' else plan['noise'], frames)
            aggregate = counts.sum(axis=0)
            draws = np.repeat(np.arange(1024), aggregate)
            row = evaluate(obj, draws, x, cross, y, scaler, actual, label, seed)
            row['logical_feasible_probability'] = float(probabilities[:, feasible].sum(axis=1).mean())
            rows.append(row)
            record = dict(seed=seed, label=label, counts=counts.tolist(), frames=frames,
                          logical_probabilities=probabilities.tolist())
            records.append(record)
            if measurement:
                channels = np.asarray(calibrations[str(seed)]['10']['channels'])
                corrected = [invert_readout(c, channels, (frame,))
                             for c, frame in zip(counts, frames, strict=True)]
                quasi = np.mean([p for p, _ in corrected], axis=0)
                weights = np.maximum(0, quasi)
                weights /= weights.sum()
                reconstructed = rng.choice(1024, size=plan['shots'], p=weights)
                record.update(readout_diagnostics=[d for _, d in corrected],
                              corrected_quasi=quasi.tolist(), reconstructed_draws=reconstructed.tolist())
                rows.append(evaluate(obj, reconstructed, x, cross, y, scaler, actual,
                                     'readout_corrected', seed))
    objective_receipt = {key: value.tolist() if isinstance(value, np.ndarray) else value
                         for key, value in obj.items()}
    return rows, records, dict(objective=objective_receipt, exact_minimum=optimum,
        base_circuits_sha256=digest(output/'selector_base.qpy'),
        feasible_states=len(feasible), compiled_gate_counts=dict(qc.count_ops()),
        compiled_depth=qc.depth(), generic_state_preparation=True,
        forward_circuits=len(plan['seeds'])*(1+sum(4 if a[1] else 1 for a in ARMS.values())),
        forward_shots=len(plan['seeds'])*(1+len(ARMS))*plan['shots'],
        auxiliary_classical_resamples=len(plan['seeds'])*plan['shots'])
