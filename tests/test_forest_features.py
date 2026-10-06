"""Check date boundaries, missing-year lags and matched width/order controls."""
import unittest
import numpy as np
import pandas as pd
from wildfire_lab.forest_features import join,panels,STRUCTURE


class FeatureTests(unittest.TestCase):
    def context(self):
        return [dict(epoch=e,forest_age_epoch=1985,
            **{c:float(e) for c in STRUCTURE},prior_epoch_biomass_change_per_year=1.)
            for e in [1985,1990,1995]]

    def test_strict_epoch_and_calendar_lag(self):
        table=pd.DataFrame(dict(year=[1988,1989,1991],total_observed_size_ha=[5.,8.,9.]))
        result=join(table,self.context())
        self.assertEqual(result.forest_epoch.tolist(),[1985,1985,1990])
        self.assertTrue(np.isnan(result.lag_reported_fire_area_ha.iloc[0]))
        self.assertEqual(result.lag_reported_fire_area_ha.iloc[1],5.)
        self.assertTrue(np.isnan(result.lag_reported_fire_area_ha.iloc[2]))
        self.assertEqual(result.forest_age_staleness_years.tolist(),[3,4,6])

    def test_later_epochs_do_not_change_prior_join(self):
        table=pd.DataFrame(dict(year=[1988,1990],total_observed_size_ha=[1.,2.]))
        original=join(table,self.context())
        rows=self.context();rows[1]['forest_biomass']=99999.
        modified=join(table,rows)
        pd.testing.assert_frame_equal(original,modified)

    def test_matched_panels(self):
        rows=panels({k:[0,1,4,8] for k in ['mi','exact','sqd','uniform']})
        self.assertEqual(len(rows),12)
        self.assertEqual(len(rows['weather_structure']),len(rows['zero8']))
        self.assertEqual(len(rows['all10']),len(rows['zero10']))
        self.assertEqual(set(rows['weather_structure']),set(rows['interleaved8']))
        self.assertNotEqual(rows['weather_structure'],rows['interleaved8'])


if __name__=='__main__':
    unittest.main()
