import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_data_coverage import audit


class CoverageTests(unittest.TestCase):
    def test_update_gaps_remain_unknown_and_distinct_from_incident_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);directory=root/'wildfires/ontario';directory.mkdir(parents=True)
            raw='status_year,situation_report_date,national_fire_id\n1989,1989-05-01,ON-example\n'
            (directory/'reports.csv').write_text(raw)
            (directory/'metadata.json').write_text(json.dumps(dict(csv_sha256=hashlib.sha256(raw.encode()).hexdigest())))
            config=dict(start_year=1988,end_year=1989,train=dict(start_year=1988,end_year=1988),
                        test=dict(start_year=1989,end_year=1989))
            missing,present=audit(config,root)
            self.assertEqual(missing['fire_update_rows'],'')
            self.assertEqual(missing['nfdb_incident_rows'],'')
            self.assertIn('NFDB incidents reported separately',missing['individual_update_note'])
            self.assertIn('not no-fire evidence',missing['individual_update_note'])
            self.assertEqual(present['fire_update_rows'],1)
            self.assertEqual(present['distinct_fire_ids'],1)
            self.assertEqual(present['distinct_report_dates'],1)
            self.assertIn('operational updates in snapshot',present['individual_update_note'])
