import csv
import tempfile
import unittest
from pathlib import Path
from wildfire_lab.fire import operational_incidents
from wildfire_lab.weather import month_lag, WeatherIndex


class JoinTests(unittest.TestCase):
    def test_lags_cross_year_and_geo_distance_gate(self):
        self.assertEqual(month_lag("2010-01-10", 2), "2009-11-01")
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "weather.csv"
            p.write_text("month,climate_id,latitude,longitude,mean_temp_c,total_precip_mm,snowfall_cm,heating_degree_days,cooling_degree_days\n2009-11-01,A,45,-78,-2,0,,1,0\n")
            index = WeatherIndex(p)
            incident = dict(date="2010-01-10", latitude=45, longitude=-78)
            values, metadata = index.query(incident, 2)
            self.assertEqual(values["lag2_total_precip_mm"], 0)
            self.assertEqual(metadata["month"], "2009-11-01")
            self.assertAlmostEqual(metadata["distance_km"], 0)
            incident["latitude"] = 55
            self.assertIsNone(index.query(incident, 2))

    def test_updates_become_one_example_without_size_predictor(self):
        common = dict(national_fire_id="2010_ON_A", status_year="2010", fire_year="2010",
                      situation_report_date="2010-05-01", latitude="45", longitude="-78", fire_was_prescribed="-1")
        rows = [dict(common,id="1",record_start="2010-05-01",fire_size="0.1"),
                dict(common,id="2",record_start="2010-05-03",fire_size="20")]
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "fires.csv"
            with p.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            examples, _ = operational_incidents(p)
            self.assertEqual(len(examples), 1)
            self.assertEqual(examples[0]["target"], 1)
            self.assertNotIn("fire_size", examples[0])
