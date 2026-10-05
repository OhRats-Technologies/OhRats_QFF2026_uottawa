import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from wildfire_lab.evidence_checks import validate


class EvidenceChecksTests(unittest.TestCase):
    def test_saved_metrics_are_checked_against_actual_validation_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            frame=pd.DataFrame(dict(incident_id=['a','b','c','d'],year=[2010,2011,2013,2013],latitude=[45.]*4,target=[0,1,0,1]))
            frame.to_csv(path/'features.csv',index=False)
            plan=dict(train_years=[2010,2018],validation_folds=[[2010,2012,2013,2014]],seeds=[7],final_test_sealed=True)
            record=dict(id='attempt-test',status='complete',plan=plan,axis='groups',code_hashes={'plan.json':'planhash'},dataset={'data_sha256':hashlib.sha256((path/'features.csv').read_bytes()).hexdigest()},rows=[dict(status='complete',seed=7,fold=plan['validation_folds'][0],full_train_rows=2,full_validation_rows=2,features=['latitude'],metric=dict(rows=2,prevalence=.5,average_precision=.6,roc_auc=.5))])
            reservation=dict(id='attempt-test',plan=plan,plan_sha256='planhash')
            self.assertEqual(validate(record,reservation,path)['rows_checked'],1)
            broken=copy.deepcopy(record);broken['rows'][0]['metric']['prevalence']=.7
            with self.assertRaisesRegex(ValueError,'Validation labels'):validate(broken,reservation,path)
            broken=copy.deepcopy(record);broken['rows'][0]['features']=['target']
            with self.assertRaisesRegex(ValueError,'Leaking predictor'):validate(broken,reservation,path)
            broken=copy.deepcopy(record);broken['rows'][0]['seed']=99
            with self.assertRaisesRegex(ValueError,'Undeclared'):validate(broken,reservation,path)
            frame.loc[3,'year']=2019;frame.to_csv(path/'features.csv',index=False)
            record['dataset']['data_sha256']=hashlib.sha256((path/'features.csv').read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'sealed-year'):validate(record,reservation,path)
