"""Execute the frozen constant-ancilla control on saved training angles only."""
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/constant_ancilla_control.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parents(plan):
    parents = {}
    for record in plan['parents']:
        path = ROOT / record['path']
        if digest(path) != record['sha256']:
            raise ValueError(f'Changed parent: {record["condition"]}, fold {record["fold"]}')
        with np.load(path) as saved:
            parents[record['fold'], record['condition']] = {
                'angles': saved['train_angles'].copy(), 'gram': saved['gram'].copy()}
    return parents


def saved_identity(parents):
    records = []
    for fold in range(3):
        four = parents[fold, 'weather_four']
        zero = parents[fold, 'weather_plus_zero']
        angles = four['angles']
        assert np.array_equal(angles, zero['angles'][:, :4])
        assert np.all(zero['angles'][:, 4] == 0)
        last = angles[:, -1]
        factor = np.cos(np.pi * (last[:, None] - last[None, :])) ** 2
        classical = np.column_stack([np.ones(len(last)), np.cos(2 * np.pi * last),
                                     np.sin(2 * np.pi * last)]) / np.sqrt(2)
        records.append({
            'fold': fold, 'training_rows': len(angles), 'matrix_entries': len(angles) ** 2,
            'maximum_width_change': float(np.max(np.abs(zero['gram'] - four['gram']))),
            'maximum_cosine_factor_residual': float(np.max(np.abs(
                zero['gram'] - four['gram'] * factor))),
            'maximum_classical_factor_gram_residual': float(np.max(np.abs(
                factor - classical @ classical.T))),
            'minimum_classical_factor_eigenvalue': float(np.linalg.eigvalsh(factor).min()),
        })
    return records


def control_metrics(base, disconnected, reference):
    base_gram = np.abs(base @ base.conj().T) ** 2
    disconnected_gram = np.abs(disconnected @ disconnected.conj().T) ** 2
    tensor = np.asarray([np.kron(np.ones(2) / np.sqrt(2), vector) for vector in base])
    return {
        'rows': len(base),
        'maximum_tensor_factorization_residual': float(np.max(np.abs(disconnected - tensor))),
        'maximum_disconnected_gram_residual': float(np.max(np.abs(disconnected_gram - base_gram))),
        'maximum_saved_reference_residual': float(np.max(np.abs(base_gram - reference))),
        'maximum_state_normalization_residual': float(max(
            np.max(np.abs(np.sum(np.abs(base) ** 2, axis=1) - 1)),
            np.max(np.abs(np.sum(np.abs(disconnected) ** 2, axis=1) - 1)))),
    }


def check_metrics(records, control, plan):
    limits = plan['tolerances']
    assert max(row['maximum_cosine_factor_residual'] for row in records) < limits['saved_matrix_absolute']
    assert max(row['maximum_classical_factor_gram_residual'] for row in records) < limits['gram_equality_absolute']
    assert control['maximum_saved_reference_residual'] < limits['saved_matrix_absolute']
    assert control['maximum_tensor_factorization_residual'] < limits['tensor_factorization_absolute']
    assert control['maximum_disconnected_gram_residual'] < limits['gram_equality_absolute']
    assert control['maximum_state_normalization_residual'] < limits['gram_equality_absolute']


def generate_control(angles, plan):
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import zz_feature_map
    from qiskit.quantum_info import Statevector

    recipe = plan['recipe']
    base_map = zz_feature_map(4, reps=recipe['reps'], alpha=recipe['alpha'],
                             entanglement=recipe['entanglement'])
    disconnected_map = QuantumCircuit(5)
    disconnected_map.compose(base_map, qubits=range(4), inplace=True)
    disconnected_map.h(4)
    disconnected_map.p(2 * recipe['ancilla_angle'], 4)
    base, disconnected = [], []
    states = 0
    start = perf_counter()
    for row in angles:
        if perf_counter() - start > plan['budget']['elapsed_soft_limit_seconds']:
            raise TimeoutError('Ancilla control exceeded elapsed budget; preserve intent')
        for circuit, storage in [(base_map, base), (disconnected_map, disconnected)]:
            assert states < plan['budget']['new_statevectors_max']
            storage.append(Statevector.from_instruction(circuit.assign_parameters(row)).data)
            states += 1
    return np.asarray(base), np.asarray(disconnected), {
        'new_statevectors': states, 'qiskit_version': qiskit.__version__,
        'base_operations': dict(base_map.count_ops()),
        'disconnected_operations': dict(disconnected_map.count_ops()),
        'seconds': perf_counter() - start,
    }


def main():
    plan = json.loads(PLAN.read_text())
    directory = ROOT / plan['output']
    directory.mkdir(parents=True, exist_ok=True)
    code = ROOT / 'scripts/context/ancilla.py'
    intent = {'plan': plan, 'source_hashes': {str(path.relative_to(ROOT)): digest(path)
              for path in [PLAN, code, ROOT / 'uv.lock']}}
    with (directory / 'intent.json').open('x') as stream:
        json.dump(intent, stream, indent=2)
    parents = load_parents(plan)
    records = saved_identity(parents)
    rows = plan['control_rows']
    original = parents[0, 'weather_four']
    angles = original['angles'][:rows]
    base, disconnected, resources = generate_control(angles, plan)
    vectors = directory / 'statevectors.npz'
    np.savez(vectors, base=base, disconnected=disconnected, angles=angles)
    control = control_metrics(base, disconnected, original['gram'][:rows, :rows])
    check_metrics(records, control, plan)
    result = {
        'id': plan['id'], 'status': 'passed', 'source_hashes': intent['source_hashes'],
        'parents': plan['parents'], 'saved_identity': records, 'tensor_control': control,
        'statevectors_sha256': digest(vectors), 'resources': resources,
        'sampler_pair_circuits': 0, 'shots': 0, 'predictor_fits': 0, 'hardware_jobs': 0,
        'interpretation': plan['interpretation'],
        'discovery_status': plan['already_inspected'],
    }
    (directory / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ['source_hashes', 'parents']}, indent=2))


if __name__ == '__main__':
    main()
