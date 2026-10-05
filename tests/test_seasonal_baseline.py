import copy
import unittest
import numpy as np
import pandas as pd
from wildfire_lab.seasonal_baseline import run,validate


class BaselineTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(37)
        self.frame=pd.DataFrame(dict(incident_id=[str(i) for i in range(80)],year=[2014]*48+[2018]*32,
            target=[0,1]*40,month_sin=rng.normal(size=80),month_cos=rng.normal(size=80),
            latitude=rng.normal(size=80),longitude=rng.normal(size=80)))
        self.frame.loc[0,'month_sin']=np.nan
        self.plan=dict(train_years=[1988,2018],folds=[[1988,2014,2015,2018]],max_logistic_fits=3,
            feature_groups=dict(intercept=[],season=['month_sin','month_cos'],geography=['latitude','longitude'],
                                geography_season=['latitude','longitude','month_sin','month_cos']),
            logistic=dict(C=1.,max_iter=1000,random_state=7))

    def test_read_only_reconstruction_and_tampering(self):
        rows=run(self.frame,self.plan)
        self.assertEqual(validate(self.frame,self.plan,rows)['conditions'],4)
        self.assertTrue(np.allclose(rows[0]['predictions'],.5))
        changed=copy.deepcopy(rows);changed[1]['parameters']['coefficient'][0]+=1
        with self.assertRaisesRegex(ValueError,'predictions'):validate(self.frame,self.plan,changed)
        with self.assertRaisesRegex(ValueError,'Missing'):validate(self.frame,self.plan,rows[:-1])

    def test_validation_cannot_change_fitted_parameters_and_future_rows_refused(self):
        original=run(self.frame,self.plan)
        changed=self.frame.copy();changed.loc[48:,'month_sin']+=100
        again=run(changed,self.plan)
        for a,b in zip(original,again):self.assertEqual(a['parameters'],b['parameters'])
        changed.loc[79,'year']=2019
        with self.assertRaisesRegex(ValueError,'training-period'):run(changed,self.plan)
        plan=copy.deepcopy(self.plan);plan['max_logistic_fits']=2
        with self.assertRaisesRegex(ValueError,'cap'):run(self.frame,plan)
