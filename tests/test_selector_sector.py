"""Check compressed dynamics against full Qiskit circuits and sampled SQD."""
import unittest
import numpy as np
from qiskit.quantum_info import Statevector
from wildfire_lab.constrained_qaoa import circuit
from wildfire_lab.selector_sector import Sector, sample, diagonal_sqd


def fixture(n=6, k=2):
    rng = np.random.default_rng(7)
    return dict(linear=rng.normal(size=n), pair=np.triu(rng.normal(size=(n,n)),1),
                constant=2., k=k)


class SectorTests(unittest.TestCase):
    def test_matches_qiskit_up_to_global_phase(self):
        for n, k in [(4,2), (10,4)]:
            obj = fixture(n,k)
            sector = Sector(obj)
            for parameters in [[.4,.2], [-.7,.35]]:
                full = Statevector.from_instruction(circuit(obj, parameters, 'feasible', 'XY')).data
                small = sector.state(parameters)
                phase = np.vdot(small, full[sector.states])
                np.testing.assert_allclose(full[sector.states], phase*small, atol=2e-10)
                self.assertAlmostEqual(float(abs(phase)), 1.)

    def test_two_layers_match_full_circuit(self):
        obj = fixture(4,2)
        first = circuit(obj,[.4,.2],'feasible','XY')
        second = circuit(obj,[.7,-.3],'feasible','XY')
        for instruction in second.data[1:]:
            first.append(instruction.operation,
                         [second.find_bit(q).index for q in instruction.qubits])
        sector = Sector(obj)
        np.testing.assert_allclose(Statevector.from_instruction(first).probabilities()[sector.states],
                                   sector.probability([.4,.2,.7,-.3]),atol=2e-10)

    def test_multiple_layers_preserve_cardinality_and_norm(self):
        sector = Sector(fixture(20,4))
        self.assertEqual(len(sector.states), 4845)
        self.assertTrue(np.all(sector.bits.sum(axis=1) == 4))
        self.assertAlmostEqual(sector.probability([.4,.2,.7,-.3]).sum(),1.)

    def test_saved_samples_match_real_diagonal_sqd(self):
        obj = fixture()
        sector = Sector(obj)
        record = sample(sector, sector.probability([.4,.2]),128,17)
        result = diagonal_sqd(obj, record)
        self.assertEqual(sum(record['counts'].values()),128)
        self.assertAlmostEqual(result['sqd_energy'],record['objective'])


if __name__ == '__main__':
    unittest.main()
