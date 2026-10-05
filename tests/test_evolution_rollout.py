import unittest
import hashlib
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import patch
from wildfire_lab.evolution_rollout import run_world
from wildfire_lab.evolution_checks import verify_world, verify_shared, collect
from wildfire_lab.evaluation import scores
from wildfire_lab.evolution_study import verify_confirmation


class EvolutionRolloutTests(unittest.TestCase):
    def test_missing_saved_outcomes_cannot_be_collected_as_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);table=root/'features.csv'
            table.write_text('year,incident_id\n2014,a\n2015,b\n')
            plan=dict(dataset='.',dataset_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),fold=[1988,2014,2015,2018])
            with self.assertRaisesRegex(FileNotFoundError,'No saved policy rollout outcomes'):
                collect(root,plan)

    def test_shared_copy_metadata_and_flags_are_checked(self):
        def evaluate(name):return dict(candidate=name,ap=.3,predictor_fits=1)
        world=run_world(evaluate,['evolved_v1','classical_gate'])
        self.assertEqual(len(verify_shared(world)),3)
        world['trees'][1]['nodes'][0]['ap']=.4
        with self.assertRaisesRegex(ValueError,'Shared evaluator copies'):
            verify_shared(world)

    def test_confirmation_rejects_committed_evaluator_drift(self):
        files=['wildfire_lab/evolution_evaluator.py','wildfire_lab/evolution_rollout.py',
               'wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py','wildfire_lab/evaluation.py',
               'experiments/policy_evolution.json','pyproject.toml','uv.lock','wildfire_lab/evolution_policy.py']
        hashes=dict.fromkeys(files,'frozen')
        parent=dict(intent=dict(recipe_sha256=hashes.copy()))
        selected=dict(policy_sha256='frozen')
        verify_confirmation(parent,selected,hashes)
        hashes['wildfire_lab/kernel.py']='committed_but_different'
        with self.assertRaisesRegex(ValueError,'evaluator differs'):
            verify_confirmation(parent,selected,hashes)

    def test_collection_recomputes_predictions_and_rejects_tampering(self):
        y=np.array([0,1,0,1])
        def evaluate(name):
            p=np.array([.1,.9,.3,.8])
            metric=scores(y,p,False)
            return dict(candidate=name,ap=metric['average_precision'],metric=metric,
                predictions=p.tolist(),prediction_sha256=hashlib.sha256(p.tobytes()).hexdigest(),predictor_fits=1)
        world=run_world(evaluate,['evolved_v1'])
        world.update(seed=1,labels=y.tolist(),train_rows=4,validation_rows=4,train_positive=2,
            validation_positive=2,train_indices_sha256='fixture',validation_indices_sha256='fixture')
        plan=dict(query_budget=3,query_penalty=.005)
        with patch('wildfire_lab.evolution_evaluator.evaluate',side_effect=AssertionError('refit')):
            self.assertEqual(verify_world(world,plan)['trees'][0]['requests'],1)
        world['trees'][0]['nodes'][0]['predictions'][0]=.2
        with self.assertRaisesRegex(ValueError,'prediction bytes'):
            verify_world(world,plan)

    def test_fresh_requests_are_generated_once_and_revealed_separately(self):
        called = []
        aps = {'standard_logistic': .2, 'robust_tanh/rbf': .3,
               'standard_tanh/rbf': .25, 'robust_tanh/qiskit_ZZ': .4}
        def evaluate(name):
            called.append(name)
            return dict(candidate=name, ap=aps[name], predictor_fits=1)
        result = run_world(evaluate, ['evolved_v1', 'classical_gate'])
        self.assertEqual(called, list(aps))
        self.assertEqual(result['predictor_fits'], 4)
        self.assertEqual([t['requests'] for t in result['trees']], [2, 3])
        self.assertFalse(result['trees'][0]['nodes'][1]['shared_execution'])
        self.assertTrue(result['trees'][1]['nodes'][1]['shared_execution'])
        self.assertEqual(result['trees'][0]['best_ap'], .3)

    def test_internal_parent_and_duplicate_are_rejected(self):
        def evaluate(name): return dict(candidate=name, ap=.3)
        actions = [dict(parent='root', candidate='a'), dict(parent='node-1', candidate='b'),
                   dict(parent='node-1', candidate='c')]
        with patch('wildfire_lab.evolution_rollout.next_action', side_effect=actions):
            with self.assertRaisesRegex(ValueError, 'ineligible'):
                run_world(evaluate, ['stub'])
        actions = [dict(parent='root', candidate='a'), dict(parent='node-1', candidate='a')]
        with patch('wildfire_lab.evolution_rollout.next_action', side_effect=actions):
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                run_world(evaluate, ['stub'])


if __name__ == '__main__': unittest.main()
