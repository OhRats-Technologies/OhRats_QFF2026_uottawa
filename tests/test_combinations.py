import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from wildfire_lab.combination_screen import run
from wildfire_lab.evaluation import sample_indices


class CombinationTests(unittest.TestCase):
    def test_selection_cannot_see_uncapped_labels_and_identical_subsets_reuse(self):
        rng=np.random.default_rng(42);columns=['a','b','c','d']
        train=pd.DataFrame(rng.normal(size=(100,4)),columns=columns)
        train['target']=np.arange(100)%2
        valid=train.iloc[:20].copy()
        plan=dict(features=columns,feature_budget=2,qaoa={},selectors=['l1_ranking','classical_qubo','qaoa_same_qubo'],encoding_screen=dict(train_cap=12,validation_cap=8))
        ti=sample_indices(len(train),12,42)
        calls=[]
        def choose(x,y,*args):
            np.testing.assert_array_equal(y,train.iloc[ti].target)
            obj=dict(linear=np.zeros(4),pair=np.zeros((4,4)),constant=0.,k=2)
            return dict(l1_ranking=[0,1],classical_qubo=[2,3],qaoa_same_qubo=[2,3]),obj,{}
        def predict(t,v,p,seed):
            self.assertEqual(t.index.tolist(),ti.tolist());self.assertEqual(len(v),8)
            calls.append(p['encoding_screen']['features'])
            return [dict(predictor='qiskit_ZZ',features=p['encoding_screen']['features'],metric={'average_precision':float(t.target.mean())},simulated_state_preparations=20,hardware_fidelity_pairs_if_naive=124)]
        modified=train.copy();modified.loc[~modified.index.isin(ti),'target']=1000
        with patch('wildfire_lab.combination_screen.subset_choices',choose),patch('wildfire_lab.combination_screen.predictors',predict):
            first=run(train,valid,plan,42);second=run(modified,valid,plan,42)
        self.assertEqual(len(calls),4)  # Two distinct subsets in each run.
        self.assertEqual([r['metric'] for r in first],[r['metric'] for r in second])
        self.assertTrue(first[-1]['prediction_reused'])
        self.assertEqual(first[-1]['simulated_state_preparations'],0)
        self.assertEqual(len({r['train_indices_sha256'] for r in first}),1)
