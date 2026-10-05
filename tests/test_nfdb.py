import unittest
from wildfire_lab.nfdb import flags, agency_date


class NFDBTests(unittest.TestCase):
    def test_mismatched_dates_missing_size_and_prescribed_are_explicit(self):
        row = dict(YEAR="1988", MONTH="2", DAY="29", REP_DATE="1988-02-29 0:00:00",
                   LATITUDE="45", LONGITUDE="-78", SIZE_HA="0", PRESCRIBED=" ", FIRE_TYPE="IFR")
        self.assertEqual(agency_date(row).isoformat(), "1988-02-29")
        self.assertEqual(flags(row), [])
        row.update(REP_DATE="1989-02-28 0:00:00", SIZE_HA="-999", PRESCRIBED="PB")
        self.assertIn("agency_date_disagrees_with_rep_date", flags(row))
        self.assertIn("unknown_or_negative_reported_size", flags(row))
        self.assertIn("prescribed_or_unspecified_prescribed_code", flags(row))
        row.update(YEAR="1989", LATITUDE="nan")
        self.assertIsNone(agency_date(row))
        self.assertIn("invalid_location", flags(row))


class HistoricalSelectionTests(unittest.TestCase):
    def test_collisions_are_quarantined_and_test_labels_not_selected(self):
        from unittest.mock import patch
        from wildfire_lab.nfdb import incidents
        base=dict(SRC_AGENCY='ON',YEAR='1988',MONTH='6',DAY='1',REP_DATE='1988-06-01',LATITUDE='45',LONGITUDE='-78',SIZE_HA='12',PRESCRIBED='',FIRE_TYPE='IFR')
        rows=[dict(base,NFDBFIREID='good'),dict(base,NFDBFIREID='collision'),dict(base,NFDBFIREID='collision',SIZE_HA='1'),dict(base,NFDBFIREID='test',YEAR='2019',REP_DATE='2019-06-01')]
        with patch('wildfire_lab.nfdb.records',return_value=rows):
            selected,excluded=incidents(None)
        self.assertEqual([r['incident_id'] for r in selected],['good'])
        self.assertEqual(selected[0]['target'],1)
        self.assertNotIn('SIZE_HA',selected[0])
        self.assertEqual(excluded['identity_collision_quarantined'],2)
