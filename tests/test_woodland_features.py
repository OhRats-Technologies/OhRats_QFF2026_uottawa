"""Native class/coordinate sampling with quality and temporal gates."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform
from wildfire_lab.woodland import WoodlandIndex


class WoodlandFeatureTests(unittest.TestCase):
    def test_center_water_is_flagged_and_future_year_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'map.tif'
            x,y=transform('EPSG:4326','EPSG:3978',[-78],[45])
            profile=dict(driver='GTiff',height=11,width=11,count=1,dtype='uint8',crs='EPSG:3978',transform=from_origin(x[0]-165,y[0]+165,30,30),nodata=255)
            raw=np.full((11,11),210,dtype='uint8');raw[5,5]=20
            with rasterio.open(path,'w',**profile) as f:f.write(raw,1)
            index=WoodlandIndex(path,year=1987,radius_m=60)
            point=dict(latitude=45,longitude=-78,year=1988)
            values=index.features([point,dict(point,year=1986)])
            self.assertEqual(values[0]['cover_center_class'],20)
            self.assertEqual(values[0]['cover_center_water'],1)
            self.assertGreater(values[0]['cover_conifer'],0)
            self.assertIsNone(values[1])
