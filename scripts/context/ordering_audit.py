"""Post-hoc, gate-free check of the saved one-layer ZZ amplitudes."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def amplitudes(angles, graph):
    bits = ((np.arange(16)[:, None] >> np.arange(4)) & 1).astype(float)
    edges = list(zip(range(3), range(1, 4))) if graph == 'linear' else list(itertools.combinations(range(4), 2))
    phase = angles @ bits.T
    for a, b in edges:
        phase += ((np.pi - angles[:, a]) * (np.pi - angles[:, b]))[:, None] * np.abs(bits[:, a] - bits[:, b])
    # H supplies uniform amplitudes; P(2 theta) and CX-P-CX add bit/parity phases.
    return np.exp(2j * phase) / 4


def audit(directory):
    result = json.loads((directory / 'result.json').read_text())
    collected = json.loads((directory / 'collection.json').read_text())
    assert digest(directory / 'arrays.npz') == result['arrays_sha256']
    assert digest(directory / 'result.json') == collected['result_sha256']
    arrays = np.load(directory / 'arrays.npz', allow_pickle=False)
    rows = []
    for row in result['rows']:
        angles = np.pi / row['denominator'] * np.tanh(arrays['z'][:, row['order']['indices']] / 2)
        direct = amplitudes(angles, row['graph'])
        error = float(np.max(abs(direct - arrays[row['key'] + '_states'])))
        assert error < 1e-10, row['key']
        overlap = abs(direct @ direct.conj().T) ** 2
        kernel_error = float(np.max(abs(overlap - arrays[row['key'] + '_kernel'])))
        assert kernel_error < 1e-10, row['key']
        rows.append({'key': row['key'], 'amplitude_residual': error, 'kernel_residual': kernel_error})
    receipt = {
        'status': 'passed', 'result_sha256': digest(directory / 'result.json'),
        'arrays_sha256': result['arrays_sha256'], 'audit_code_sha256': digest(Path(__file__)),
        'rows': rows, 'classical_amplitude_reconstructions': 496,
        'new_qiskit_calls': 0, 'predictor_fits': 0, 'hardware_jobs': 0,
        'scope': 'Post-hoc direct NumPy bit/parity-phase audit of all saved one-layer ZZ states. '
                 'No circuit simulator or shared fidelity/statistics/basis helper used; no labels, '
                 'fresh predictive validation, optimal-order selection or new quantum claim.',
    }
    (directory / 'formula-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'maximum_amplitude_residual': max(r['amplitude_residual'] for r in rows),
                      'maximum_kernel_residual': max(r['kernel_residual'] for r in rows), 'new_qiskit_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/input-order-v1')
    parser.add_argument('--figure', action='store_true', help='Draw saved matrices; requires the analysis group')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.cache'):
        parser.error('Output must remain under ignored .cache/')
    audit(output)
    if args.figure:
        from ordering_figure import draw
        print(draw(output).relative_to(ROOT))
