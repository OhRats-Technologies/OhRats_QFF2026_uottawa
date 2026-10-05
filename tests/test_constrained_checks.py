import copy
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from wildfire_lab.constrained_selection import run
from wildfire_lab.constrained_checks import validate_seed


class ConstrainedAuditTests(unittest.TestCase):
    def test_saved_choices_parameters_and_probabilities_reconstruct_without_model_refit(self):
        rng=np.random.default_rng(31);columns=['a','b','c','d'];x=rng.normal(size=(80,4))
        frame=pd.DataFrame(x,columns=columns);frame['target']=np.arange(80)%2
        frame['incident_id']=[str(i) for i in range(80)];frame['year']=[2014]*50+[2018]*30
        train,valid=frame.iloc[:50],frame.iloc[50:]
        parent=dict(train_cap=30,validation_cap=20)
        plan=dict(features=columns,feature_count=2,shots=16,initial_states=['all','feasible'],mixers=['X','XY'],
            max_objective_calls=6,logical_gate_basis=['rz','sx','x','cx'],transpiler_optimization_level=1,mechanism_tolerance=1e-10,
            logistic=dict(C=1.,max_iter=1000),l1=dict(C=.1,solver='liblinear',l1_ratio=1.,max_iter=1000),
            classical_controls=['exact','l1','uniform_all','uniform_feasible'])
        record=run(train,valid,parent,plan,17,'diagnostic',lambda *_:None)
        with patch('sklearn.linear_model.LogisticRegression.fit',side_effect=AssertionError('Audit refit')):
            result=validate_seed(train,valid,parent,plan,record)
        self.assertEqual(result['predictor_fits'],8);self.assertEqual(result['audit_reconstruction_states'],4)
        bad=copy.deepcopy(record);bad['rows'][0]['intercept']+=.1
        with self.assertRaises(AssertionError):validate_seed(train,valid,parent,plan,bad)
        bad=copy.deepcopy(record);bad['quantum'][0]['probabilities'][0]+=.01
        with self.assertRaises(AssertionError):validate_seed(train,valid,parent,plan,bad)
