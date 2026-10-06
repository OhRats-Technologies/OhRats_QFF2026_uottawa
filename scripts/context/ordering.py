"""Run or collect the frozen training-input-only feature-order diagnostic."""
import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/context_input_order.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_plan():
    plan = json.loads(PLAN.read_text())
    assert PLAN.read_bytes() == subprocess.check_output(
        ['git', 'show', 'HEAD:experiments/context_input_order.json'], cwd=ROOT)
    for path, expected in plan['source_sha256'].items():
        assert sha(ROOT / path) == expected, path
    for package, version in plan['software'].items():
        assert importlib.metadata.version(package) == version, package
    return plan


def run(output):
    import pandas as pd
    from qiskit.circuit.library import zz_feature_map
    from qiskit.quantum_info import Statevector
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from ordering_math import fidelity, rbf, statistics, basis_indices

    plan = frozen_plan()
    # Outcome/count columns are not materialized by this input-only loader.
    table = pd.read_csv(ROOT / plan['input'], usecols=['year', *plan['features']])
    assert table.year.tolist() == list(range(1988, 2019))
    output.mkdir(parents=True)  # Exclusive intent; never overwrite an existing run.
    (output / 'intent.json').write_text(json.dumps({'plan_sha256': sha(PLAN), 'plan': plan}, indent=2) + '\n')
    began = time.perf_counter()
    raw = table[plan['features']].to_numpy()
    imputed = SimpleImputer(strategy='median').fit_transform(raw)
    z = StandardScaler().fit_transform(imputed)
    distances = np.sum((z[:, None] - z[None, :]) ** 2, axis=-1)
    gamma = 1 / np.median(distances[distances > 0])
    classical = rbf(z, gamma)
    arrays = {'raw': raw, 'z': z, 'years': table.year.to_numpy(), 'rbf_reference': classical}
    rows, prepared, gate_counts = [], 0, {}
    for denominator in plan['amplitude_pi_denominators']:
        angles = np.pi / denominator * np.tanh(z / 2)
        for graph in plan['graphs']:
            circuit = zz_feature_map(4, reps=1, entanglement=graph, alpha=2)
            gate_counts[graph] = dict(circuit.count_ops())
            for order in plan['orders']:
                key = f"{graph}_d{denominator}_{order['name']}"
                inputs = angles[:, order['indices']]
                assert prepared + len(inputs) <= plan['budget']['statevector_preparations']
                states = np.array([Statevector.from_instruction(circuit.assign_parameters(values)).data
                                   for values in inputs])
                prepared += len(inputs)
                assert time.perf_counter() - began < plan['budget']['soft_seconds']
                matrix = fidelity(states)
                if order['name'] == 'identity':
                    reference, reference_states = matrix, states
                expected_symmetry = graph == 'full' or order['name'] in ['identity', 'reverse']
                state_error = float(np.max(np.abs(states - reference_states[:, basis_indices(order['indices'])])))
                stats = statistics(matrix, reference)
                rbf_error = float(np.max(np.abs(rbf(z[:, order['indices']], gamma) - classical)))
                assert rbf_error < plan['tolerance']
                if expected_symmetry:
                    assert stats['max_entry_change'] < plan['tolerance'] and state_error < plan['tolerance']
                assert np.max(np.abs(np.sum(abs(states) ** 2, axis=1) - 1)) < plan['tolerance']
                arrays[key + '_states'], arrays[key + '_kernel'] = states, matrix
                rows.append(dict(key=key, graph=graph, denominator=denominator, order=order,
                                 expected_symmetry=expected_symmetry, state_relabelling_error=state_error,
                                 rbf_permutation_error=rbf_error, **stats))
    np.savez_compressed(output / 'arrays.npz', **arrays)
    result = {
        'status': 'completed', 'plan_sha256': sha(PLAN), 'source_sha256': plan['source_sha256'],
        'software': plan['software'], 'years': table.year.tolist(), 'gamma': float(gamma), 'rows': rows,
        'arrays_sha256': sha(output / 'arrays.npz'), 'statevector_preparations': prepared,
        'untranspiled_gate_counts': gate_counts,
        'kernel_matrices': len(rows), 'gram_entries': len(rows) * len(z) ** 2,
        'seconds': time.perf_counter() - began, 'predictor_fits': 0,
        'preprocessing_fits': 2, 'sampler_pair_circuits': 0, 'shots': 0, 'hardware_jobs': 0,
        'scope': plan['interpretation'],
    }
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['status', 'statevector_preparations', 'kernel_matrices',
                                                 'seconds', 'predictor_fits', 'hardware_jobs']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'collect'])
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/input-order-v1')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.cache'):
        parser.error('Output must remain under ignored .cache/')
    if args.action == 'run':
        run(output)
    else:
        from ordering_collect import collect
        collect(output)


if __name__ == '__main__':
    main()
