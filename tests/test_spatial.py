import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from wildfire_lab.spatial import split,coordinates


class SpatialTests(unittest.TestCase):
    def test_grid_cells_and_guard_are_disjoint(self):
        train=pd.DataFrame(dict(incident_id=['near','far','other'],latitude=[0]*3,longitude=[0]*3))
        valid=pd.DataFrame(dict(incident_id=['held','notheld'],latitude=[0]*2,longitude=[0]*2))
        xy=[np.array([[190000.,0],[100000.,0],[210000.,0]]),np.array([[210000.,0],[100000.,0]])]
        with patch('wildfire_lab.spatial.coordinates',side_effect=xy):
            a,b,meta=split(train,valid,side=0,width_m=200000,guard_m=50000)
        self.assertEqual(a.incident_id.tolist(),['far'])
        self.assertEqual(b.incident_id.tolist(),['held'])
        self.assertEqual(meta['minimum_train_validation_distance_m'],110000)

    def test_geographic_coordinates_round_trip(self):
        from rasterio.warp import transform
        frame=pd.DataFrame(dict(latitude=[45.,52.],longitude=[-78.,-90.]))
        xy=coordinates(frame)
        lon,lat=transform('EPSG:3978','EPSG:4326',xy[:,0],xy[:,1])
        np.testing.assert_allclose(lon,frame.longitude,atol=1e-8)
        np.testing.assert_allclose(lat,frame.latitude,atol=1e-8)

    def test_matched_control_reports_its_own_geometry(self):
        from wildfire_lab.spatial import matched_control
        train=pd.DataFrame(dict(incident_id=['a','b'],latitude=[0,0],longitude=[0,0]))
        valid=pd.DataFrame(dict(incident_id=['v'],latitude=[0],longitude=[0]))
        xy=[np.array([[100000.,0],[210000.,0]]),np.array([[210000.,0]])]
        with patch('wildfire_lab.spatial.coordinates',side_effect=xy):
            a,meta=matched_control(train,valid,2,7,dict(block_width_m=200000,train_cells=1,guard_m=50000))
        self.assertEqual(meta['train_cells'],2)
        self.assertEqual(meta['shared_cells'],1)
        self.assertEqual(meta['minimum_train_validation_distance_m'],0)
