"""Annual labels must not inherit the incident classifier's eligibility filters."""

import unittest
import numpy as np
import pandas as pd
from wildfire_lab.annual_data import fire_years, climate_years


class AnnualDataTests(unittest.TestCase):
    def test_annual_size_denominator_preserves_unknown_and_bad_coordinates(self):
        base = dict(SRC_AGENCY='ON', YEAR='1988', PRESCRIBED='', FIRE_TYPE='',
                    LATITUDE='-999', LONGITUDE='', MONTH='0', DAY='0')
        rows = [dict(base, NFDBFIREID=identity, SIZE_HA=size)
                for identity, size in [('a', '0'), ('b', '100'), ('c', '-999')]]
        rows += [dict(base, NFDBFIREID='duplicate', SIZE_HA='1000')] * 2
        table, exclusions = fire_years(rows, 1988, 1988)
        row = table.iloc[0]
        self.assertEqual(row.recorded_incidents, 3)
        self.assertEqual(row.size_observed_incidents, 2)
        self.assertEqual(row.unknown_size_incidents, 1)
        self.assertEqual(row.mean_reported_size_ha, 50)
        self.assertEqual(exclusions['blank_or_duplicate_identity'], 2)

    def test_station_weights_and_complete_annual_totals(self):
        rows = []
        for identity, months, value in [('a', 12, 10), ('b', 9, 30)]:
            for month in range(1, months + 1):
                rows.append(dict(climate_id=identity, month=f'1988-{month:02d}-01',
                                 mean_temp_c=value, total_precip_mm=value,
                                 snowfall_cm=value, highest_max_temp_c=value,
                                 lowest_min_temp_c=value, heating_degree_days=value,
                                 cooling_degree_days=value))
        result = climate_years(pd.DataFrame(rows), 1988, 1988).iloc[0]
        self.assertEqual(result.annual_mean_temp_c, 20)
        self.assertEqual(result.annual_mean_temp_c_stations, 2)
        self.assertEqual(result.annual_precip_mm, 120)
        self.assertEqual(result.annual_precip_mm_stations, 1)
        self.assertEqual(result.summer_precip_mm, 60)

    def test_empty_size_year_is_unknown_not_zero(self):
        table, _ = fire_years([], 1988, 1988)
        self.assertTrue(np.isnan(table.iloc[0].mean_reported_size_ha))
        self.assertEqual(table.iloc[0].unknown_size_incidents, 0)


if __name__ == '__main__':
    unittest.main()
