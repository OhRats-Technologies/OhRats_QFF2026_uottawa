"""Qiskit ML compute-uncompute kernels over already encoded inputs; local only."""
import time
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.primitives import QMLSampler
from qiskit_machine_learning.state_fidelities import ComputeUncompute


class CountingSampler(QMLSampler):
    def __init__(self, shots=None, seed=7):
        super().__init__(shots=shots, seed=seed)
        self.circuits = 0

    def run(self, pubs, *, shots=None):
        pubs = list(pubs)
        self.circuits += len(pubs)
        return super().run(pubs, shots=shots)


def matrices(train_angles, validation_angles, *, shots=None, seed=7, reps=2):
    sampler = CountingSampler(shots=shots, seed=seed)
    kernel = FidelityQuantumKernel(
        feature_map=zz_feature_map(train_angles.shape[1], reps=reps, entanglement='linear'),
        fidelity=ComputeUncompute(sampler), enforce_psd=False,
        evaluate_duplicates='off_diagonal', max_circuits_per_job=256)
    start = time.perf_counter()
    gram = kernel.evaluate(train_angles)
    cross = kernel.evaluate(validation_angles, train_angles)
    return gram, cross, dict(kernel_seconds=time.perf_counter()-start,
        pair_circuits=sampler.circuits, shots_per_pair=shots,
        synthetic_shots=None if shots is None else shots*sampler.circuits,
        execution='local analytic' if shots is None else 'local finite-shot sampling',
        hardware_jobs_submitted=0)


def project_psd(matrix):
    """Same eigenvalue-clipping principle as the library's PSD option."""
    values, vectors = np.linalg.eigh((matrix+matrix.T)/2)
    repaired = (vectors*np.maximum(values, 0)) @ vectors.T
    return repaired, dict(raw_min_eigenvalue=float(values.min()),
        negative_eigenvalues=int((values < -1e-10).sum()),
        psd_repair_frobenius=float(np.linalg.norm(repaired-matrix)))
