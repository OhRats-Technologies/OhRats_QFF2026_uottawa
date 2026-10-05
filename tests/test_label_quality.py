import unittest
from decimal import Decimal
from unittest.mock import patch
from wildfire_lab.label_quality import training_sizes,select_cohort,summarize,retention


class LabelQualityTests(unittest.TestCase):
    def setUp(self):
        self.plan=dict(agency='ON',years=[1988,1989],target_threshold_ha='10',
            descriptive_thresholds_ha=['1','10','20'],boundary_half_widths_ha=['1'],
            numeric_steps_ha=['0.1','1'],top_recorded_sizes=10)
        self.source={str(i):dict(year=1988 if i<5 else 1989,size=Decimal(s),target=int(Decimal(s)>=10))
                     for i,s in enumerate(['0','0.1','9','9.9','10','10.0','10.1','11','20'])}

    def test_exact_decimal_boundaries_and_zero_are_explicit(self):
        result=summarize(self.source,self.plan)
        self.assertEqual(result['positive_rows'],5)
        self.assertEqual(result['exact_threshold_rows'],2)
        self.assertEqual(result['strictly_above_threshold_rows'],3)
        self.assertEqual(result['zero_size_rows'],1)
        self.assertEqual(result['boundary_bands'][0]['rows'],5)
        self.assertEqual(result['boundary_bands'][0]['negative_rows'],2)
        self.assertEqual(result['positive_size_numeric_multiples'][1]['rows'],5)
        self.assertEqual(sum(r['rows'] for r in result['annual']),9)

    def test_cohort_identity_year_label_and_subset_are_checked(self):
        rows=[dict(incident_id='4',year='1988',target='1')]
        selected=select_cohort(self.source,rows,self.plan['years'])
        self.assertEqual(retention(self.source,selected)['1']['excluded_rows'],4)
        for bad in [rows+rows,[dict(rows[0],year='2019')],[dict(rows[0],target='0')],[dict(rows[0],incident_id='unknown')]]:
            with self.assertRaises(ValueError):select_cohort(self.source,bad,self.plan['years'])
        with self.assertRaises(ValueError):retention(selected,self.source)

    def test_final_year_size_is_never_interpreted(self):
        accepted=[dict(incident_id='a',year=1988,target=1)]
        rows=[dict(SRC_AGENCY='ON',YEAR='1988',NFDBFIREID='a',SIZE_HA='10'),
              dict(SRC_AGENCY='ON',YEAR='2019',NFDBFIREID='later',SIZE_HA='must not parse')]
        with patch('wildfire_lab.label_quality.incidents',return_value=(accepted,{})),patch('wildfire_lab.label_quality.records',return_value=rows):
            result,_=training_sizes(None,self.plan)
        self.assertEqual(result['a']['size'],Decimal('10'))
        with self.assertRaises(ValueError):training_sizes(None,dict(self.plan,years=[1988,2019]))
