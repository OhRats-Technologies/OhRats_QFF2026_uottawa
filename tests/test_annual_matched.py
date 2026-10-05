"""Inner-only quantum configuration selection must ignore outer performance."""

import unittest
from wildfire_lab.annual_matched import choose_quantum, rbf_candidates


class AnnualMatchedTests(unittest.TestCase):
    def test_outer_errors_do_not_select_the_quantum_map(self):
        fold = [1988, 2006, 2007, 2010]
        rows = [dict(fold=fold, mae_ha=outer, inner_tuning=[dict(mae_ha=inner)])
                for outer, inner in [(1., 40.), (1000., 10.), (2., 30.), (3., 20.)]]
        self.assertIs(choose_quantum(rows, fold), rows[1])

    def test_equal_candidate_count(self):
        plan = dict(rbf_gamma_multipliers=[.25, 1., 4., 16.])
        parent = dict(svr_grid=dict(C=[.1, 1., 10.], epsilon=[.05, .2, .5]))
        self.assertEqual(len(rbf_candidates(plan, parent)), 36)


if __name__ == '__main__':
    unittest.main()
