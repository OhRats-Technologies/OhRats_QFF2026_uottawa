"""Check real local cardinality-preserving samples against the exact diagonal control."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from wildfire_lab.forest_selectors import select


class SelectorTests(unittest.TestCase):
    def test_quantum_counts_and_same_objective_controls(self):
        rng=np.random.default_rng(7)
        x=rng.normal(size=(12,4))
        y=x[:,0]+.1*x[:,2]
        plan={'selection':{'selected_count':2,'cardinality_penalty':2.,'redundancy_weight':.5,
                           'relevance_neighbors':3,'seed':137,'parameters':[.4,.2],'shots':64}}
        with tempfile.TemporaryDirectory() as path:
            choices,result=select(x,y,plan,Path(path))
        self.assertEqual(sum(result['counts'].values()),64)
        self.assertTrue(all(b.count('1')==2 for b in result['counts']))
        self.assertEqual(result['feasible_subsets'],6)
        self.assertAlmostEqual(result['ideal_feasible_probability'],1.)
        self.assertAlmostEqual(result['sampled']['sqd_energy'],result['sampled']['sampled_minimum'])
        self.assertGreaterEqual(result['sampled']['gap_to_exact'],-1e-9)
        self.assertTrue(all(len(v)==2 for v in choices.values()))


if __name__=='__main__':
    unittest.main()
