"""Check chronology and that held-out values cannot fit the transform."""
import unittest
import numpy as np
import pandas as pd
from wildfire_lab.evaluation import split, transform, sample_indices


class EvaluationTests(unittest.TestCase):
    def test_sealed_years_and_identity_overlap_are_rejected(self):
        frame=pd.DataFrame(dict(year=[2010,2013],incident_id=['same','same']))
        with self.assertRaises(ValueError):split(frame,[2010,2012,2013,2014])
        with self.assertRaises(ValueError):split(frame,[2010,2018,2019,2020])

    def test_imputation_and_scale_fit_only_training_rows(self):
        train=pd.DataFrame(dict(x=[0.,2.,np.nan]))
        valid=pd.DataFrame(dict(x=[100.,np.nan]))
        x,v=transform(train,valid,['x'])
        self.assertAlmostEqual(float(x.mean()),0)
        self.assertAlmostEqual(float(v[1,0]),0)
        self.assertGreater(float(v[0,0]),100)
        self.assertEqual(sample_indices(100,20,7).tolist(),sample_indices(100,20,7).tolist())
        self.assertEqual(len(set(sample_indices(100,20,7))),20)


if __name__=='__main__':unittest.main()
