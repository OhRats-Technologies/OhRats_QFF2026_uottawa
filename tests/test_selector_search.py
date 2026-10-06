"""Optimizer resource/selection checks on a small independently enumerable sector."""
import unittest
import numpy as np
from qiskit.quantum_info import Statevector
from wildfire_lab.constrained_qaoa import circuit
from wildfire_lab.selector_sector import Sector
from wildfire_lab.selector_search import optimize, search


class SearchTests(unittest.TestCase):
    def sector(self):
        return Sector(dict(linear=np.array([-.4, -.2, .3, .7]),
                           pair=np.zeros((4, 4)), constant=0., k=2))

    def test_bounded_trace_and_returned_state_agree(self):
        sector = self.sector()
        result = optimize(sector, 3, [2., .4], 24)
        self.assertLessEqual(result['objective_calls'], 24)
        self.assertEqual(result['state_evaluations'], result['objective_calls']+1)
        probability = sector.probability(result['parameters'])
        self.assertAlmostEqual(probability @ sector.cost, result['expected_objective'])
        self.assertGreaterEqual(result['expected_objective'], sector.cost.min()-1e-10)
        np.testing.assert_allclose(probability, result['probability'])
        self.assertTrue(all(np.asarray(r['parameters']).size == 6 for r in result['trace']))

    def test_multi_start_selection_uses_training_objective_only(self):
        runs, winners = search(self.sector(), dict(
            optimization_calls={'1': 20, '2': 24}, starts=[[2., .4], [1.2, .8]]))
        self.assertEqual(len(runs), 4)
        for label, index in winners.items():
            depth = int(label[-1])
            self.assertEqual(runs[index]['depth'], depth)
            self.assertEqual(runs[index]['expected_objective'], min(
                r['expected_objective'] for r in runs if r['depth'] == depth))

    def test_deeper_sector_matches_full_qiskit_dynamics(self):
        obj = dict(linear=np.array([-.4, -.2, .3, .7]),
                   pair=np.triu(np.full((4, 4), .13), 1), constant=0., k=2)
        sector = Sector(obj)
        pairs = [[.4, .2], [.7, -.3], [-.2, .5], [.9, -.1]]
        for depth in [3, 4]:
            full = circuit(obj, pairs[0], 'feasible', 'XY')
            for pair in pairs[1:depth]:
                layer = circuit(obj, pair, 'feasible', 'XY')
                for instruction in layer.data[1:]:
                    full.append(instruction.operation,
                                [layer.find_bit(q).index for q in instruction.qubits])
            np.testing.assert_allclose(
                Statevector.from_instruction(full).probabilities()[sector.states],
                sector.probability(np.asarray(pairs[:depth]).ravel()), atol=2e-10)


if __name__ == '__main__':
    unittest.main()
