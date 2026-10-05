"""Fixed Qiskit fidelity kernel and classical controls over the same inputs."""
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector


def states(x, scale=.5, reps=2):
    return angle_states(np.pi*(.5 + scale*np.tanh(x/2)), reps)


def angle_states(angles, reps=2):
    feature_map = zz_feature_map(feature_dimension=angles.shape[1], reps=reps, entanglement="linear")
    parameters = list(feature_map.parameters)
    return np.stack([Statevector.from_instruction(feature_map.assign_parameters(dict(zip(parameters,row)))).data for row in angles])


def fidelity(left, right):
    return np.abs(left.conj() @ right.T)**2


def product_rotation_kernel(left, right, scale=.5):
    """Unentangled analytic quantum-map control; computable classically."""
    left = np.pi*(.5+scale*np.tanh(left/2))
    right = np.pi*(.5+scale*np.tanh(right/2))
    return angle_product_kernel(left,right)


def angle_product_kernel(left,right):
    return np.prod(np.cos((left[:,None,:]-right[None,:,:])/2)**2, axis=-1)
