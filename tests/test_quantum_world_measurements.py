import unittest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix
from qiskit_aer.noise import depolarizing_error
from quantum_world.measurements import tomography_design,focused_estimate,index_interval,tomography_estimate,grouped_design,grouped_estimate,single_pauli_estimate


class MeasurementTests(unittest.TestCase):
    def test_exact_budget_and_finite_fit(self):
        design=tomography_design(4096,882)
        self.assertEqual(int(design['shots'].sum()),4096)
        result=tomography_estimate(design,1.1,883)
        self.assertTrue(np.isfinite(result['rate']))
        self.assertLess(result['interval'][0],result['interval'][1])

    def test_bell_probe_equals_separable_control_in_qiskit(self):
        p=np.exp(-1.1*.8);noise=depolarizing_error(1-p,2).to_quantumchannel()
        circuit=QuantumCircuit(2);circuit.h(1);circuit.cx(1,0)
        initial=DensityMatrix.from_label('00')
        z=initial.evolve(noise).probabilities()
        bell=initial.evolve(circuit).evolve(noise).evolve(circuit.inverse()).probabilities()
        np.testing.assert_allclose(z,bell,atol=1e-12)
        np.testing.assert_allclose(z,[(1+3*p)/4,*([(1-p)/4]*3)],atol=1e-12)

    def test_binomial_interval_mapping_and_index_boundary(self):
        result=focused_estimate(65536,1.1,884)
        self.assertLess(result['interval'][0],result['interval'][1])
        self.assertEqual(index_interval([1.08,1.12]),[3,3])
        self.assertEqual(index_interval([1.04,1.12]),[3,4])
        self.assertEqual(index_interval([0.,None]),[1,None])

    def test_grouped_basis_probabilities_and_shared_marginal(self):
        design=grouped_design(4096,885)
        probability=(1+design['contrast'])/4
        self.assertGreater(float(probability.min()),-1e-12)
        np.testing.assert_allclose(probability.sum(axis=-1),1.,atol=1e-12)
        self.assertEqual(int(design['shots'].sum()),4096)
        result=grouped_estimate(design,1.1,886)
        self.assertLess(result['interval'][0],result['interval'][1])
        basis=focused_estimate(4096,1.1,886)
        single=single_pauli_estimate(basis)
        self.assertEqual(sum(single['counts']),4096)
        self.assertEqual(single['counts'][0],sum(basis['counts'][:2]))

    def test_grouped_xy_measurement_matches_qiskit(self):
        from quantum_world.physics import haar_states
        design=grouped_design(4096,885,n_states=4)
        circuit=QuantumCircuit(2);circuit.h(1);circuit.sdg(0);circuit.h(0)
        for i,psi in enumerate(haar_states(4,885)):
            probabilities=DensityMatrix(psi).evolve(circuit).probabilities()
            np.testing.assert_allclose(probabilities,(1+design['contrast'][i,1])/4,atol=1e-12)


if __name__=='__main__':unittest.main()
