"""Local circuit suppression and tensor readout inversion; no service access."""
import numpy as np
from scipy.sparse.linalg import LinearOperator, gmres
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, amplitude_damping_error, phase_damping_error


def pauli(qc, qubit, x, z):
    if x:
        qc.x(qubit)
    if z:
        qc.z(qubit)


def suppressed_circuit(compiled, noise, dd=False, twirl_seed=None, damping=False):
    """CX Pauli frames preserve the ideal gate; idle windows are declared, not scheduled."""
    qc = QuantumCircuit(compiled.num_qubits)
    rng = np.random.default_rng(twirl_seed)
    for item in compiled.data:
        qubits = [compiled.find_bit(q).index for q in item.qubits]
        if item.operation.name != 'cx':
            qc.append(item.operation, qubits)
            continue
        control, target = qubits
        xc, zc, xt, zt = rng.integers(2, size=4) if twirl_seed is not None else [0]*4
        pauli(qc, control, xc, zc)
        pauli(qc, target, xt, zt)
        qc.cx(control, target)
        qc.rz(noise['cx_target_z_radians'], target)
        pauli(qc, control, xc, zc ^ zt)
        pauli(qc, target, xt ^ xc, zt)
        spectator = next(q for q in range(qc.num_qubits) if q not in qubits)
        phase = noise['spectator_idle_z_radians']
        if dd:
            qc.rz(phase/2, spectator)
            qc.rx(np.pi, spectator)
            qc.rz(phase/2, spectator)
            qc.rx(-np.pi, spectator)
        else:
            qc.rz(phase, spectator)
        if damping:
            qc.append(amplitude_damping_error(noise['amplitude_damping']).to_instruction(), [target])
            qc.append(phase_damping_error(noise['phase_damping']).to_instruction(), [target])
    return qc


def sample(circuits, shots, seed, noise=None, frames=None, density=False):
    frames = [0]*len(circuits) if frames is None else frames
    measured = []
    for qc, frame in zip(circuits, frames, strict=True):
        qc = qc.copy()
        qc.save_probabilities()
        for q in range(qc.num_qubits):
            if frame >> q & 1:
                qc.x(q)
        qc.measure_all()
        measured.append(qc)
    model = NoiseModel()
    if noise is not None:
        p01, p10 = noise['readout_0_to_1'], noise['readout_1_to_0']
        model.add_all_qubit_readout_error(ReadoutError([[1-p01, p01], [p10, 1-p10]]))
    backend = AerSimulator(method='density_matrix' if density else 'statevector',
                           noise_model=model, max_parallel_threads=2)
    result = backend.run(measured, shots=shots, seed_simulator=seed).result()
    if not result.success:
        raise RuntimeError('Local Aer simulation failed')
    counts, probabilities = [], []
    for i, (qc, frame) in enumerate(zip(circuits, frames, strict=True)):
        row = np.zeros(2**qc.num_qubits, dtype=np.int64)
        for bits, count in result.get_counts(i).items():
            row[int(bits.replace(' ', ''), 2) ^ frame] += count
        counts.append(row)
        probabilities.append(np.asarray(result.data(i)['probabilities']))
    return np.array(counts), np.array(probabilities)


def calibrate(n, noise, shots, seed):
    zero, one = QuantumCircuit(n), QuantumCircuit(n)
    one.x(range(n))
    counts, _ = sample([zero, one], shots, seed, noise)
    bits = (np.arange(2**n)[:, None] >> np.arange(n)) & 1
    p01 = counts[0] @ bits / shots
    p10 = counts[1] @ (1-bits) / shots
    channels = np.array([[[1-a, b], [a, 1-b]] for a, b in zip(p01, p10)])
    return counts, channels


def assignment(probability, channels, frames=(0,)):
    n = len(channels)
    indices = np.arange(2**n)
    total = np.zeros_like(probability, dtype=float)
    for frame in frames:
        tensor = probability[indices ^ frame].reshape([2]*n)
        for q, channel in enumerate(channels):
            axis = n-1-q
            moved = np.moveaxis(tensor, axis, 0)
            tensor = np.moveaxis(np.tensordot(channel, moved, axes=(1, 0)), 0, axis)
        total += tensor.reshape(-1)[indices ^ frame]
    return total/len(frames)


def invert_readout(counts, channels, frames=(0,)):
    """Invert the frame-averaged tensor channel; retain negative quasi-probabilities."""
    observed = counts/counts.sum()
    operator = LinearOperator((len(observed), len(observed)),
                              matvec=lambda p: assignment(p, channels, frames))
    corrected, info = gmres(operator, observed, rtol=1e-10, atol=1e-12)
    if info:
        raise ValueError('Readout inverse did not converge')
    residual = float(np.linalg.norm(assignment(corrected, channels, frames)-observed))
    return corrected, dict(residual=residual,
                          negative_mass=float(-corrected[corrected < 0].sum()))


def repair_kernel(gram, cross, rank=None):
    values, vectors = np.linalg.eigh((gram+gram.T)/2)
    kept = np.flatnonzero(values > 1e-10)
    if rank is not None:
        kept = kept[-rank:]
    basis = vectors[:, kept]
    return (basis*values[kept]) @ basis.T, cross @ basis @ basis.T
