"""Selector weights and preprocessing cannot learn from the outer block."""
import unittest
import numpy as np
import pandas as pd
from wildfire_lab.objective_study import tune_weight


class ObjectiveTests(unittest.TestCase):
    def test_weight_tuning_has_only_inner_training_and_later_inner_validation(self):
        rng = np.random.default_rng(23)
        frame = pd.DataFrame(rng.normal(size=(19, 6)), columns=list('abcdef'))
        frame['year'] = np.arange(1988, 2007)
        frame['mean_reported_size_ha'] = np.exp(frame.a)
        plan = dict(weights=[0., .5], selection=dict(selected_count=4, relevance_neighbors=3,
                    cardinality_penalty=2., seed=137), models=dict(ridge={'alpha': 1.},
                    svr={'C': 1., 'epsilon': .2}))
        chosen, records = tune_weight(frame, list('abcdef'), plan)
        for record in records:
            for split in record['splits']:
                self.assertLess(max(split['training_years']), min(split['validation_years']))
                self.assertEqual(len(split['selected_indices']), 4)
        for proxy, weight in chosen.items():
            best = min((r for r in records if r['proxy'] == proxy), key=lambda row: row['mae_ha'])
            self.assertEqual(weight, best['weight'])


if __name__ == '__main__':
    unittest.main()
