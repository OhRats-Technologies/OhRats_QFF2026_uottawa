import tempfile
import unittest
from pathlib import Path
import pandas as pd
from wildfire_lab.climatology import MonthlyBaseline


class ClimatologyTests(unittest.TestCase):
    def test_future_years_cannot_change_training_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'weather.csv'
            pd.DataFrame(dict(climate_id=['A']*3,month=['1987-01-01','1988-01-01','2019-01-01'],mean_temp_c=[0.,2.,999.],total_precip_mm=[1.,3.,999.])).to_csv(path,index=False)
            baseline=MonthlyBaseline(path,1988,min_samples=2)
            frame=pd.DataFrame(dict(date=['1989-02-01','1989-02-01'],station_lag1=['A','unseen'],lag1_mean_temp_c=[10.,10.],lag1_total_precip_mm=[3.,3.]))
            values,meta=baseline.attach(frame,lags=[1])
            self.assertAlmostEqual(values.lag1_temp_anomaly_c.iloc[0],9.)
            self.assertAlmostEqual(values.lag1_temp_anomaly_c.iloc[1],9.)
            self.assertEqual(meta['fit_latest_year'],1988)
            self.assertEqual(meta['fallback_counts']['lag1_temp_anomaly_c'],1)
            with self.assertRaises(ValueError):MonthlyBaseline(path,2019)
