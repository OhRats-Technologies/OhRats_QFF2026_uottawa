import unittest
from wildfire_lab.discovery_replay import replay,ORDERS


class ReplayTests(unittest.TestCase):
    def test_stopping_policy_does_not_read_unqueried_outcome(self):
        class RevealedOnly(dict):
            def __getitem__(self,key):
                if key.endswith('qiskit_ZZ'):raise AssertionError('Unqueried quantum arm')
                return super().__getitem__(key)
        panel=RevealedOnly(standard_logistic=dict(ap=.6,seconds=0),
            **{'robust_tanh/rbf':dict(ap=.3,seconds=1),
               'standard_tanh/rbf':dict(ap=.4,seconds=1)})
        result=replay(panel,'classical_gate')
        self.assertEqual(result['evaluations'],2)
        self.assertEqual(result['best_ap'],.6)

    def test_finite_budget_and_best_revealed_score(self):
        panel={name:dict(ap=.2,seconds=1) for order in ORDERS.values() for name in order}
        panel['standard_logistic']=dict(ap=.1,seconds=0)
        result=replay(panel,'balanced',budget=1)
        self.assertEqual(result['evaluations'],1)
        self.assertEqual(result['best_ap'],.2)
