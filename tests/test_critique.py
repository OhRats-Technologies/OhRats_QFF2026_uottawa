"""Sensitivity meaning, retained timing and offline public arithmetic."""
import copy
import json
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from wildfire_lab.critique_stability import error_summary, tuning_sensitivity
from wildfire_lab.critique_geometry import exact_timing


class CritiqueTests(unittest.TestCase):
    def test_deleting_a_dominant_error_changes_mean_without_refitting(self):
        actual, prediction = [0., 0., 0.], [1., 1., 10.]
        summary = error_summary([2007, 2008, 2009], actual, prediction)
        self.assertEqual(summary['mae_ha'], 4.)
        self.assertEqual(summary['omitted_year_range'], [1., 5.5])
        self.assertAlmostEqual(summary['largest_error_share'], 10/12)
        self.assertEqual(prediction, [1., 1., 10.])

    def test_score_weight_sensitivity_preserves_cached_candidates(self):
        candidate = lambda name, prediction: dict(specification=dict(model=name, parameter=prediction[0]), predicted_ha=prediction)
        rows = [candidate(kind, p) for kind in ['ridge', 'rbf', 'qsvr'] for p in [[0., 5., 0.], [3., 0., 3.]]]
        evidence = dict(cohorts=[dict(panel='fixture', fold=[1988, 2000, 2001, 2003],
            tuning=dict(inner_splits=[dict(validation_years=[1998, 1999, 2000], actual_ha=[0., 0., 0.])],
                        candidates=rows, chosen={k:dict(model=k, parameter=0.) for k in ['ridge', 'rbf', 'qsvr']}))])
        before = copy.deepcopy(evidence)
        result = tuning_sensitivity(evidence)
        self.assertEqual(evidence, before)
        self.assertEqual(result[2]['changed_deletions'], 2)
        self.assertEqual(result[2]['deletion_winner_indices'], [1, 0, 1])

    def test_exact_timing_recovers_all_feasible_states(self):
        objective = dict(linear=[-1., -2., -3., -4.], pair=np.zeros((4, 4)).tolist(), constant=0., k=2)
        result = exact_timing(objective, 3)
        self.assertEqual(result['feasible_states'], 6)
        self.assertEqual(result['selected_state'], 12)
        self.assertEqual(result['exact_cost'], -7.)

    def test_slide_yield_matches_actual_cardinality_counts(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('presentation_shots', root/'scripts/presentation_shots.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')):
            rebuilt = module.build(root)
        self.assertEqual(json.loads((root/'web/presentation/assets/shot-sweep.json').read_text()), rebuilt)
        self.assertEqual(len(rebuilt['rows']), 12)
        self.assertEqual(rebuilt['physical_shots'], 301056)
        self.assertEqual(rebuilt['charged_seconds'], 108)

    def test_saved_public_response_replays_offline(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('critique_collector', root/'scripts/collect_critique.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
             patch('numpy.random.default_rng', side_effect=AssertionError('Sampling forbidden')), \
             patch('wildfire_lab.critique_geometry.perf_counter_ns', side_effect=AssertionError('Timing rerun forbidden')):
            result = module.collect(root)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['predictor_fits'], 0)


if __name__ == '__main__':
    unittest.main()
