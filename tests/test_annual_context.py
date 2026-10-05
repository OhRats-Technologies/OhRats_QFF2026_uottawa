"""Coverage filtering must not treat unknown days as complete or inspect validation."""

import unittest
import numpy as np
import pandas as pd
from wildfire_lab.annual_context import complete_days, training_roster


class ContextTests(unittest.TestCase):
    def test_unknown_day_count_is_not_zero(self):
        rows = []
        for missing in [0., 1., np.nan]:
            row = dict.fromkeys(['mean_temp_c', 'heating_degree_days', 'cooling_degree_days',
                                 'total_precip_mm', 'snowfall_cm', 'highest_max_temp_c',
                                 'lowest_min_temp_c'], 10.)
            row.update(dict.fromkeys(['missing_mean_temp_days', 'missing_precip_days',
                                      'missing_snowfall_days', 'missing_max_temp_days',
                                      'missing_min_temp_days'], missing))
            rows.append(row)
        clean, counts = complete_days(pd.DataFrame(rows))
        self.assertEqual(clean.mean_temp_c.notna().tolist(), [True, False, False])
        self.assertEqual(counts['total_precip_mm'], 2)

    def test_roster_does_not_use_validation_station(self):
        rows = []
        for identity, year in [('train', 1988), ('future', 1989)]:
            for month in range(1, 13):
                rows.append(dict(climate_id=identity, month=f'{year}-{month:02d}-01',
                                 mean_temp_c=10., total_precip_mm=20.))
        self.assertEqual(training_roster(pd.DataFrame(rows), 1988, 1988), ['train'])


if __name__ == '__main__':
    unittest.main()
