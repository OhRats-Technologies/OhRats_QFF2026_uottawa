import unittest
import hashlib
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from wildfire_lab.coordinate_quality import audit,summary,datum_check


class CoordinateTests(unittest.TestCase):
    def test_datum_metadata_and_measured_sensitivity_do_not_change_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'source.zip'
            xml='<metadata><geogcsn>GCS_North_American_1983</geogcsn><refSysInfo><RefSystem><refSysID><identCode code="3978"/></refSysID></RefSystem></refSysInfo><attr><attrlabl>LATITUDE</attrlabl><attrdef>Latitude</attrdef><attrdefs>Agency</attrdefs></attr></metadata>'
            with zipfile.ZipFile(path,'w') as z:z.writestr('NFDB_point_fixture.txt.xml',xml)
            before=path.read_bytes();sha=hashlib.sha256(before).hexdigest()
            frame=pd.DataFrame(dict(latitude=[45.],longitude=[-78.]))
            with patch('rasterio.warp.transform',return_value=([3.],[4.])),patch('wildfire_lab.coordinate_quality.coordinates',return_value=np.zeros((1,2))):
                result=datum_check(frame,path,sha)
            self.assertEqual(result['projected_difference_m']['1'],5.)
            self.assertEqual(result['stored_geometry_reference_codes'],['3978'])
            self.assertEqual(result['field_definitions']['LATITUDE']['source'],'Agency')
            self.assertEqual(path.read_bytes(),before)
            with self.assertRaisesRegex(ValueError,'Changed'):datum_check(frame,path,'0'*64)

    def test_distinct_incidents_repeated_coordinates_and_apparent_grid_alignment(self):
        frame=pd.DataFrame(dict(latitude=[45.,45.,45.12345],longitude=[-78.,-78.,-78.12345]))
        result=summary(frame)
        self.assertEqual(result['unique_coordinates'],2)
        self.assertEqual(result['rows_on_repeated_coordinates'],2)
        self.assertEqual(result['additional_rows_beyond_unique_coordinates'],1)
        self.assertEqual(result['both_coordinates_grid_aligned']['0.01']['rows'],2)

    def test_chronological_nearest_distance_direction_and_no_labels_needed(self):
        frame=pd.DataFrame(dict(incident_id=['a','b','v1','v2'],year=[2014,2014,2018,2018],
            latitude=[45.,46.,45.,47.],longitude=[-78.,-79.,-78.,-80.]))
        points=[np.array([[0.,0],[10000.,0]]),np.array([[0.,0],[13000.,0]])]
        with patch('wildfire_lab.coordinate_quality.coordinates',side_effect=points):
            result=audit(frame,[[1988,2014,2015,2018]])
        row=result['chronological_conditions'][0]
        self.assertEqual(row['validation_rows_at_exact_training_coordinate'],1)
        self.assertEqual(row['nearest_training_distance_km']['0.5'],1.5)
        self.assertEqual(row['fraction_with_training_point_within_km']['1'],.5)
        self.assertFalse(result['method']['uses_labels'])
        self.assertEqual(result['method']['model_fits'],0)
        frame.loc[3,'year']=2019
        with self.assertRaisesRegex(ValueError,'training-period'):audit(frame,[[1988,2014,2015,2018]])
