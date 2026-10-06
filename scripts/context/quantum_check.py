"""Verify the game's illustrative channel/control arithmetic against exact Qiskit."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
from time import perf_counter

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Kraus, Operator, Pauli

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/instrument_diagnostic.json'


def rotation(angle):
    circuit = QuantumCircuit(1)
    circuit.rz(angle, 0)
    return Operator(circuit)


def simulate(theta, phi, options):
    circuit = QuantumCircuit(1)
    circuit.ry(theta, 0)
    circuit.rz(phi, 0)
    state = DensityMatrix.from_instruction(circuit)
    if options['dd']:
        echo = QuantumCircuit(1)
        echo.rz(options['idle'] / 2, 0)
        echo.rx(np.pi, 0)
        echo.rz(options['idle'] / 2, 0)
        echo.rx(-np.pi, 0)
        state = state.evolve(Operator(echo))
    else:
        state = state.evolve(rotation(options['idle']))
    gate = options['gate']
    if options['twirl']:
        state = state.evolve(Kraus([rotation(gate).data / np.sqrt(2),
                                   rotation(-gate).data / np.sqrt(2)]))
    else:
        state = state.evolve(rotation(gate))
    damping = options['damping']
    amplitude = Kraus([np.diag([1, np.sqrt(1 - damping)]),
                       np.array([[0, np.sqrt(damping)], [0, 0]])])
    phase = options['dephasing'] / 2
    dephasing = Kraus([np.sqrt(1 - phase) * np.eye(2),
                       np.sqrt(phase) * np.diag([1, -1])])
    state = state.evolve(amplitude).evolve(dephasing)
    return [float(state.expectation_value(Pauli(axis)).real) for axis in ['X', 'Y', 'Z']]


def main():
    plan = json.loads(PLAN.read_text())
    files = [PLAN, Path(__file__), ROOT / 'web/demo/strategy/quantum.js',
             ROOT / 'web/demo/strategy/diagnostic.js']
    hashes = {str(file.relative_to(ROOT)): hashlib.sha256(file.read_bytes()).hexdigest()
              for file in files}
    directory = ROOT / '.cache/quantum-instrument-v1'
    directory.mkdir(exist_ok=True)
    intent = directory / 'intent.json'
    with intent.open('x') as stream:
        json.dump({'plan': plan, 'source_hashes': hashes}, stream, indent=2)
    rows = []
    start = perf_counter()
    for theta, phi, damping, phase, control in itertools.product(
            plan['theta'], plan['phi'], plan['damping'], plan['dephasing'], plan['controls']):
        options = {'idle': plan['idle_z_drift'], 'gate': plan['gate_z_overrotation'],
                   'dd': 'echo' in control, 'twirl': 'twirled' in control,
                   'damping': damping, 'dephasing': phase}
        rows.append({'theta': theta, 'phi': phi, 'control': control, 'options': options,
                     'qiskit': simulate(theta, phi, options)})
    assert len(rows) == plan['budget']['density_matrix_paths']
    reference = subprocess.run(['bun', str(ROOT / 'web/demo/strategy/diagnostic.js')],
                               input=json.dumps(rows), text=True, capture_output=True, check=True)
    browser = np.asarray(json.loads(reference.stdout))
    values = np.asarray([row['qiskit'] for row in rows])
    error = float(np.max(np.abs(values - browser)))
    assert error < 1e-12
    assert float(np.max(np.sum(values ** 2, axis=1))) <= 1 + 1e-12
    result = {'id': plan['id'], 'status': 'passed', 'paths': len(rows),
              'maximum_coordinate_error': error, 'seconds': perf_counter() - start,
              'qiskit_version': qiskit.__version__, 'source_hashes': hashes,
              'hardware_jobs': 0, 'shots': 0, 'fits': 0,
              'interpretation': 'Browser formulas match exact Qiskit for these declared one-qubit channels and ideal control assumptions. This is a physical-arithmetic verification, not novel predictive evidence or a real-device noise comparison.'}
    (directory / 'records.json').write_text(json.dumps(rows, indent=2) + '\n')
    (ROOT / 'docs/data/instrument_diagnostic.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
