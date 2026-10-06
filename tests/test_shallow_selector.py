"""Full-circuit parity, cardinality and global-phase tests for basis starts."""
import unittest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from wildfire_lab.selector_sector import Sector
from wildfire_lab.shallow_selector import probability, circuit, cost_phase, optimize


class ShallowTests(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(47)
        n, k, penalty = 6, 2, 2.
        return dict(linear=rng.normal(size=n)+penalty*(1-2*k),
                    pair=np.triu(rng.random((n, n))+2*penalty, 1),
                    constant=penalty*k*k, penalty=penalty, k=k)

    def test_all_three_depths_match_full_qiskit(self):
        obj = self.fixture()
        sector = Sector(obj)
        initial = [0, 3]
        for parameters in [[.4], [.4, .7, -.3], [.4, .7, -.3, -.2, .6]]:
            full = Statevector.from_instruction(circuit(obj, initial, parameters)).probabilities()
            small = probability(sector, initial, parameters)
            np.testing.assert_allclose(full[sector.states], small, atol=2e-10)
            self.assertAlmostEqual(float(full[sector.states].sum()), 1.)

    def test_first_basis_cost_phase_cannot_change_probabilities(self):
        obj = self.fixture()
        for gamma in [0., .8, -1.4]:
            qc = QuantumCircuit(6)
            qc.x([0, 3])
            cost_phase(qc, obj, gamma)
            body = circuit(obj, [0, 3], [.4, .7, -.3])
            for instruction in body.data[2:]:
                qc.append(instruction.operation, [body.find_bit(q).index for q in instruction.qubits])
            reference = Statevector.from_instruction(body).probabilities()
            np.testing.assert_allclose(Statevector.from_instruction(qc).probabilities(), reference, atol=2e-10)

    def test_optimizer_has_no_redundant_gamma_zero(self):
        sector = Sector(self.fixture())
        result = optimize(sector, [0, 3], 3, 32)
        self.assertEqual(len(result['parameters']), 5)
        self.assertLessEqual(result['objective_calls'], 32)
        self.assertAlmostEqual(np.asarray(result['probability']) @ sector.cost,
                               result['expected_objective'])


if __name__ == '__main__':
    unittest.main()
