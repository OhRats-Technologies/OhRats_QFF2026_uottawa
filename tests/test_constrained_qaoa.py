import unittest
import numpy as np
from qiskit.quantum_info import Statevector
from wildfire_lab.selection import configurations
from wildfire_lab.constrained_qaoa import circuit,select
from wildfire_lab.qaoa import circuit as original


class ConstrainedTests(unittest.TestCase):
    def setUp(self):
        self.objective=dict(linear=np.array([-1.,.2,-.5,.3]),pair=np.triu(np.ones((4,4))*.1,1),constant=0.,k=2)

    def test_factorial_separates_preparation_from_cardinality_preservation(self):
        mask=configurations(4).sum(axis=1)==2
        for parameters in [[0.,0.],[.37,.91],[2.1,-.4]]:
            for initial,expected in [('all',6/16),('feasible',1.)]:
                p=Statevector.from_instruction(circuit(self.objective,parameters,initial,'XY')).probabilities()
                self.assertAlmostEqual(p[mask].sum(),expected,places=12)
        p=Statevector.from_instruction(circuit(self.objective,[0.,0.],'feasible','X')).probabilities()
        np.testing.assert_allclose(p[mask],np.ones(6)/6,atol=1e-12)
        self.assertAlmostEqual(p[~mask].sum(),0.,places=12)

    def test_old_x_circuit_preserved_and_bounded_feasible_sampling(self):
        parameters=[.31,.23]
        a=Statevector.from_instruction(circuit(self.objective,parameters,'all','X')).data
        b=Statevector.from_instruction(original(self.objective,parameters)).data
        np.testing.assert_allclose(a,b,atol=1e-12)
        plan=dict(shots=16,max_objective_calls=6,logical_gate_basis=['rz','sx','x','cx'],transpiler_optimization_level=1)
        result=select(self.objective,'feasible','XY',17,plan)
        self.assertEqual(result['feasible_draws'],16);self.assertEqual(len(result['selected_indices']),2)
        self.assertLessEqual(result['objective_calls'],6);self.assertEqual(result['quantum_state_evaluations'],result['objective_calls']+1)
        self.assertIn('cx',result['logical_gate_counts'])
