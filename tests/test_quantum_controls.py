import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.selection import configurations, energies, ising, exact_subset

try:
    from wildfire_lab.qaoa import circuit
    from wildfire_lab.kernel import states, fidelity
    from qiskit.quantum_info import Statevector
except ImportError:
    Statevector = None


class SelectionTests(unittest.TestCase):
    def test_all_zero_integer_relevance_is_a_valid_objective(self):
        from wildfire_lab.selection import fit_objective
        with patch('wildfire_lab.selection.mutual_info_classif',return_value=np.zeros(4,dtype=int)):
            objective=fit_objective(np.random.default_rng(1).normal(size=(20,4)),np.arange(20)%2,2)
        self.assertEqual(objective['relevance'].dtype,np.dtype(float))
        np.testing.assert_array_equal(objective['relevance'],np.zeros(4))
        self.assertEqual(len(exact_subset(objective)[0]),2)

    def test_ising_and_binary_cost_match_for_every_bitstring(self):
        obj = dict(linear=np.array([-1.,2.,-3.]), pair=np.array([[0.,2.,1.],[0.,0.,-1.],[0.,0.,0.]]), constant=5., k=2)
        bits = configurations(3)
        single, pair, constant = ising(obj)
        z = 1-2*bits
        ising_cost = z @ single + np.einsum("bi,ij,bj->b", z,pair,z)+constant
        np.testing.assert_allclose(energies(obj,bits),ising_cost)
        subset,cost = exact_subset(obj)
        self.assertEqual(len(subset),2)
        self.assertEqual(cost, min(energies(obj,bits)[bits.sum(axis=1)==2]))


@unittest.skipIf(Statevector is None,"Install quantum dependency group")
class QuantumControlsTests(unittest.TestCase):
    def test_fidelity_equals_explicit_density_feature_inner_product(self):
        rng=np.random.default_rng(37)
        vectors=rng.normal(size=(7,16))+1j*rng.normal(size=(7,16))
        vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)
        density=np.einsum('bi,bj->bij',vectors,vectors.conj()).reshape(7,256)
        inner=density.conj()@density.T
        np.testing.assert_allclose(inner.imag,0,atol=1e-12)
        np.testing.assert_allclose(fidelity(vectors,vectors),inner.real,atol=1e-12)

    def test_qaoa_identity_and_kernel_psd_and_diagonal(self):
        obj = dict(linear=np.array([-1.,2.,-3.]), pair=np.zeros((3,3)), constant=0., k=2)
        probability = Statevector.from_instruction(circuit(obj,[0.,0.])).probabilities()
        np.testing.assert_allclose(probability,np.ones(8)/8)
        x = np.random.default_rng(7).normal(size=(8,4))
        s = states(x);matrix=fidelity(s,s)
        np.testing.assert_allclose(np.diag(matrix),1,atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(matrix).min(),-1e-12)
        self.assertGreater(np.max(np.abs(matrix-np.eye(8))),.01)
