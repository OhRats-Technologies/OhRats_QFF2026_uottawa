"""Leakage, kernel-library parity and reconstructible prediction checks."""
import unittest
import numpy as np
import pandas as pd
from wildfire_lab.nested_search import prepared, evaluate, tune
from wildfire_lab.search_kernels import matrices, parity, candidates, distinct_geometry


class NestedTests(unittest.TestCase):
    def plan(self):
        return dict(candidate_features=['a', 'b', 'c', 'd', 'e'], panels={'mi4': [],
                    'weather4': ['a', 'b', 'c', 'd']}, quantum=dict(
                    amplitudes={'pi32': np.pi/32}, depths=[1, 2],
                    topologies=['product', 'linear', 'ring'], orders=['canonical', 'reversed']))

    def table(self):
        rng = np.random.default_rng(13)
        values = rng.normal(size=(18, 5))
        table = pd.DataFrame(values, columns=['a', 'b', 'c', 'd', 'e'])
        table['year'] = np.arange(1988, 2006)
        table['mean_reported_size_ha'] = np.exp(values[:, 0]+.3*values[:, 1])
        return table

    def test_held_out_labels_do_not_enter_selection_or_scaling(self):
        table = self.table()
        train, valid = table.iloc[:12], table.iloc[12:].copy()
        first = prepared(train, valid, 'mi4', self.plan())
        valid['mean_reported_size_ha'] *= 100000
        second = prepared(train, valid, 'mi4', self.plan())
        self.assertEqual(first['selection'], second['selection'])
        self.assertEqual(first['preprocessing'], second['preprocessing'])
        self.assertEqual(first['selection']['labelled_years'], train.year.tolist())

    def test_statevector_kernel_matches_compute_uncompute_families(self):
        records = parity(self.plan()['quantum'])
        self.assertEqual(len(records), 24)
        self.assertLess(max(r['maximum_error'] for r in records), 2e-10)

    def test_product_permutation_control_and_saved_dual_equation(self):
        table, plan = self.table(), self.plan()
        data = prepared(table.iloc[:12], table.iloc[12:], 'weather4', plan)
        specification = dict(amplitude='pi32', reps=1, topology='product', order='canonical')
        gram, cross, _ = matrices(data['x'], data['cross'], specification, plan['quantum'])
        changed = dict(specification, order='reversed')
        reversed_gram, reversed_cross, _ = matrices(data['x'], data['cross'], changed, plan['quantum'])
        np.testing.assert_allclose(gram, reversed_gram, atol=2e-10)
        np.testing.assert_allclose(cross, reversed_cross, atol=2e-10)
        row = evaluate(data, dict(model='qsvr', circuit=specification, C=1., epsilon=.2), plan)
        parameters = row['parameters']
        reconstructed = cross[:, parameters['support']] @ parameters['dual_coef']+parameters['intercept']
        np.testing.assert_allclose(reconstructed, row['predicted_scaled'])

    def test_reversal_is_graph_symmetry_not_new_architecture(self):
        plan = self.plan()['quantum']
        values = np.linspace(-1.4, 1.2, 32).reshape(4, 8)
        for topology in ['product', 'linear', 'ring']:
            for depth in [1, 2]:
                specification = dict(amplitude='pi32', reps=depth,
                                     topology=topology, order='canonical')
                first = matrices(values[:3], values[3:], specification, plan)
                second = matrices(values[:3], values[3:], dict(specification, order='reversed'), plan)
                np.testing.assert_allclose(first[0], second[0], atol=2e-10)
                np.testing.assert_allclose(first[1], second[1], atol=2e-10)

    def test_inner_runner_uses_chronological_label_boundaries(self):
        plan = self.plan()
        plan.update(svr={'C': [.1, 1.], 'epsilon': [.2]},
                    rbf_multipliers=[.5, 2.], ridge_alpha=[.1, 1.])
        plan['quantum'].update(depths=[1], topologies=['product'], orders=['canonical'])
        result = tune(self.table(), 'mi4', plan)
        self.assertEqual(result['predictor_fits'], 24)
        for split in result['inner_splits']:
            self.assertLess(max(split['train_years']), min(split['validation_years']))
            self.assertEqual(split['train_years'], split['selection']['labelled_years'])
        for kind, selected in result['chosen'].items():
            best = min(r['mae_ha'] for r in result['candidates']
                       if r['specification']['model'] == kind)
            chosen = next(r for r in result['candidates'] if r['specification'] == selected)
            self.assertEqual(chosen['mae_ha'], best)

    def test_interleaving_changes_entangled_graph_but_product_is_pruned(self):
        plan = self.plan()['quantum']
        plan.update(orders=['canonical', 'interleaved'], unique_product_orders=True)
        self.assertEqual(len(candidates(plan)), 10)
        records = distinct_geometry(plan)
        self.assertTrue(all(row['distinct_candidates'] == 10 for row in records))


if __name__ == '__main__':
    unittest.main()
