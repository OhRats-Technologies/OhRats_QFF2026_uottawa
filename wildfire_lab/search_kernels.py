"""Explicit encoding candidates and exact/compute-uncompute parity checks."""
from itertools import product
import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector
from qiskit_machine_learning.kernels import FidelityStatevectorKernel, FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from wildfire_lab.library_kernel import CountingSampler


def candidates(plan):
    return [dict(amplitude=name, reps=depth, topology=topology, order=order)
            for name, depth, topology, order in product(
                plan['amplitudes'], plan['depths'], plan['topologies'], plan['orders'])
            if not plan.get('unique_product_orders') or topology != 'product' or order == 'canonical']


def feature_map(width, specification):
    topology = specification['topology']
    if topology == 'product':
        parameters = ParameterVector('x', width)
        circuit = QuantumCircuit(width)
        for _ in range(specification['reps']):
            circuit.h(range(width))
            for index, parameter in enumerate(parameters):
                circuit.p(2*parameter, index)
        return circuit
    pairs = [(i, i+1) for i in range(width-1)]
    if topology == 'ring':
        pairs.append((width-1, 0))
    return zz_feature_map(width, reps=specification['reps'],
                          entanglement={1: [(i,) for i in range(width)], 2: pairs})


def angles(x, specification, plan):
    width = x.shape[1]
    amplitude = plan['amplitudes'][specification['amplitude']]
    if isinstance(amplitude, list):
        # Two blocks refer to original feature identities, before permutation.
        amplitude = np.repeat(amplitude, width//2)
    theta = np.asarray(amplitude)*np.tanh(x/2)
    if specification['order'] == 'canonical':
        return theta
    if specification['order'] == 'interleaved':
        return theta[:, [*range(0, width, 2), *range(1, width, 2)]]
    return theta[:, ::-1]


def matrices(x, cross, specification, plan):
    class CountedStatevector(Statevector):
        calls = 0

        def __init__(self, *args, **kwargs):
            type(self).calls += 1
            super().__init__(*args, **kwargs)

    started = time.perf_counter()
    kernel = FidelityStatevectorKernel(
        feature_map=feature_map(x.shape[1], specification),
        statevector_type=CountedStatevector, auto_clear_cache=False,
        enforce_psd=False, shots=None)
    train, validation = angles(x, specification, plan), angles(cross, specification, plan)
    gram = kernel.evaluate(train)
    test = kernel.evaluate(validation, train)
    return gram, test, dict(state_evaluations=CountedStatevector.calls,
                           seconds=time.perf_counter()-started, hardware_jobs=0)


def parity(plan):
    records = []
    for width, topology, depth, order in product(
            [4, 8], plan['topologies'], plan['depths'], plan['orders']):
        specification = dict(amplitude='pi32', reps=depth, topology=topology, order=order)
        values = np.linspace(-1.1, .9, 3*width).reshape(3, width)
        exact, cross, resource = matrices(values[:2], values[2:], specification, plan)
        sampler = CountingSampler(shots=None, seed=7)
        kernel = FidelityQuantumKernel(
            feature_map=feature_map(width, specification),
            fidelity=ComputeUncompute(sampler), enforce_psd=False,
            evaluate_duplicates='off_diagonal')
        encoded = angles(values, specification, plan)
        reference = kernel.evaluate(encoded[:2])
        reference_cross = kernel.evaluate(encoded[2:], encoded[:2])
        np.testing.assert_allclose(exact, reference, atol=2e-10)
        np.testing.assert_allclose(cross, reference_cross, atol=2e-10)
        records.append(dict(qubits=width, specification=specification,
                            maximum_error=float(max(np.max(abs(exact-reference)),
                                                    np.max(abs(cross-reference_cross)))),
                            analytic_pair_circuits=sampler.circuits, **resource))
    return records


def distinct_geometry(plan):
    """Labels-free finite-sample duplicate check; not a universal expressivity proof."""
    records = []
    for width in [4, 8]:
        values = np.sin(np.arange(7*width).reshape(7, width)*.71)*1.3
        seen = []
        calls = 0
        for specification in candidates(plan):
            gram, _, resource = matrices(values, values[:0], specification, plan)
            calls += resource['state_evaluations']
            duplicate = next((i for i, previous in enumerate(seen)
                              if np.max(abs(gram-previous)) < 1e-10), None)
            if duplicate is not None:
                raise ValueError(f'Duplicate labels-free geometry: width{width}, candidate{specification}')
            seen.append(gram)
        records.append(dict(width=width, distinct_candidates=len(seen),
                            state_evaluations=calls, tolerance=1e-10, labels_used=0))
    return records
