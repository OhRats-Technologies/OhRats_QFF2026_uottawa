"""Exact final training/cross kernels cached independently of learned SVR states."""

import json
import time

import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.metrics.pairwise import rbf_kernel

from wildfire_lab.annual_classical import gamma
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_model_state import fit_scaling
from wildfire_lab.library_kernel import CountingSampler


def fidelity(width, reps):
    sampler = CountingSampler(shots=None, seed=7)
    kernel = FidelityQuantumKernel(
        feature_map=zz_feature_map(width, reps=reps, entanglement='linear'),
        fidelity=ComputeUncompute(sampler), enforce_psd=False,
        evaluate_duplicates='off_diagonal', max_circuits_per_job=256)
    return kernel, sampler


class TrainingKernels:
    def __init__(self, directory):
        self.directory = directory
        self.entries = []
        self.keys = {}

    def get(self, table, features, kind, params):
        key = (tuple(features), kind, tuple(sorted(params.items())))
        if key in self.keys:
            entry = self.entries[self.keys[key]]
            matrix = np.load(self.directory / entry['id'] / 'matrix.npz')['gram']
            return matrix, entry
        identifier = f'kernel-{len(self.entries):03d}'
        path = self.directory / identifier
        path.mkdir(parents=True)
        x, _, scaling = fit_scaling(table[features].to_numpy(), table.mean_reported_size_ha.to_numpy())
        start = time.perf_counter()
        if kind == 'quantum':
            angles = params['amplitude'] * np.tanh(x / 2)
            kernel, sampler = fidelity(len(features), params['reps'])
            gram = kernel.evaluate(angles)
            minimum = float(np.linalg.eigvalsh(gram).min())
            if minimum < -1e-8:
                raise ValueError('Final exact fidelity matrix is not PSD')
            resources = dict(pair_circuits=sampler.circuits, raw_min_eigenvalue=minimum,
                             execution='local analytic', hardware_jobs_submitted=0)
            arrays = dict(gram=gram, train_angles=angles)
        else:
            value = gamma(x) * params['gamma_multiplier']
            gram = rbf_kernel(x, gamma=value)
            resources = dict(gamma=value, execution='classical', hardware_jobs_submitted=0)
            arrays = dict(gram=gram, train_x=x)
        np.savez(path / 'matrix.npz', **arrays)
        entry = dict(id=identifier, kind=kind, features=features, params=params,
                     scaling=scaling, train_rows=len(table),
                     matrix_sha256=digest(path / 'matrix.npz'),
                     kernel_seconds=time.perf_counter() - start, **resources)
        (path / 'receipt.json').write_text(json.dumps(entry, indent=2) + '\n')
        self.keys[key] = len(self.entries)
        self.entries.append(entry)
        return gram, entry


def evaluate_cross(entry, saved, new_x, directory):
    directory.mkdir(parents=True)
    start = time.perf_counter()
    if entry['kind'] == 'quantum':
        angles = entry['params']['amplitude'] * np.tanh(new_x / 2)
        kernel, sampler = fidelity(len(entry['features']), entry['params']['reps'])
        cross = kernel.evaluate(angles, saved['train_angles'])
        resources = dict(pair_circuits=sampler.circuits, execution='local analytic')
        arrays = dict(cross=cross, cross_angles=angles)
    else:
        cross = rbf_kernel(new_x, saved['train_x'], gamma=entry['gamma'])
        resources = dict(execution='classical')
        arrays = dict(cross=cross, cross_x=new_x)
    np.savez(directory / 'cross.npz', **arrays)
    receipt = dict(id=entry['id'], kind=entry['kind'], validation_rows=len(new_x),
                   train_rows=entry['train_rows'], matrix_sha256=digest(directory / 'cross.npz'),
                   kernel_seconds=time.perf_counter() - start, hardware_jobs_submitted=0, **resources)
    (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return cross, receipt
