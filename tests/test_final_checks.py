import copy
import unittest
import numpy as np
import pandas as pd
from scripts.run_final_evaluation import evaluate
from wildfire_lab.final_checks import validate


class FinalCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng=np.random.default_rng(19);cols=['x0','x1','x2','x3']
        cls.train=pd.DataFrame(rng.normal(size=(48,4)),columns=cols)
        cls.test=pd.DataFrame(rng.normal(size=(24,4)),columns=cols)
        for prefix,frame,years in [('train',cls.train,[2018]*48),('test',cls.test,[2019]*12+[2020]*12)]:
            frame['incident_id']=[prefix+str(i) for i in range(len(frame))]
            frame['year']=years;frame['target']=[0,1]*(len(frame)//2)
        cls.plan=dict(status='frozen_final',train_years=[1988,2018],test_years=[2019,2024],hardware_default=False,
            cover_policy={'mode':'fixed_historical'},training_dataset_fingerprint='fixture',training_data_sha256='a'*64,threshold_ha=10,
            primary_model='tree / location',feature_groups={'location':cols},features=cols,feature_budget=2,seeds=[211],
            selectors=['l1_ranking','classical_qubo','qaoa_same_qubo'],qaoa=dict(depth=1,shots=512,maxiter=3),
            report_per_year=True,save_predictions=True,
            encoding_screen=dict(train_cap=32,validation_cap=24,C=1.,angle_scale=.05,reps=2,preprocessing=['robust_tanh'],kernels=['rbf','qiskit_ZZ']))
        cls.record=dict(status='complete',hardware_jobs_submitted=0,plan=cls.plan,test_dataset=dict(rows=len(cls.test)),
                        rows=evaluate(cls.train,cls.test,cls.plan))

    def test_recompute_scores_and_reject_tampered_outputs(self):
        checks=validate(self.record,self.train,self.test)
        self.assertEqual(checks['full_models'],2);self.assertEqual(checks['capped_models'],9)
        record=copy.deepcopy(self.record);record['rows']['full_training_models'][0]['metric']['average_precision']=0.
        with self.assertRaisesRegex(ValueError,'recomputed'):validate(record,self.train,self.test)
        record=copy.deepcopy(self.record);record['rows']['capped_crossed_matrix'][0]['validation_indices_sha256']='changed'
        with self.assertRaisesRegex(ValueError,'sample'):validate(record,self.train,self.test)

    def test_refuse_overlap_missing_model_and_changed_labels(self):
        test=self.test.copy();test.loc[0,'incident_id']=self.train.incident_id.iloc[0]
        with self.assertRaisesRegex(ValueError,'identities'):validate(self.record,self.train,test)
        record=copy.deepcopy(self.record);record['rows']['full_training_models'].pop()
        with self.assertRaisesRegex(ValueError,'missing'):validate(record,self.train,self.test)
        test=self.test.copy();test.loc[0,'target']=1
        with self.assertRaisesRegex(ValueError,'recomputed'):validate(self.record,self.train,test)
