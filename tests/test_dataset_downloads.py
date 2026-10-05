import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.download_weather import one_month, validate
from scripts.audit_data_coverage import split_year


class SplitTests(unittest.TestCase):
    def test_requested_dates_and_overlap_rejection(self):
        config = dict(train=dict(start_year=1988, end_year=2018), test=dict(start_year=2019, end_year=2024))
        self.assertEqual(split_year(1988, config), "train")
        self.assertEqual(split_year(2018, config), "train")
        self.assertEqual(split_year(2019, config), "test")
        self.assertEqual(split_year(2024, config), "test")
        config["test"]["start_year"] = 2018
        with self.assertRaises(ValueError):
            split_year(2018, config)


def weather_csv(rows=()):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Long", "Lat", "Stn_Name", "Clim_ID", "Prov_or_Ter", "Tm", "DwTm", "P", "DwP"])
    writer.writerows(rows)
    return stream.getvalue().encode()


class WeatherTests(unittest.TestCase):
    def test_missing_values_and_alphanumeric_id_preserved_and_resumable(self):
        raw = weather_csv([[-78, 45, "Station", "A001", "ON", "NA", 31, "0.0", 31]])
        with tempfile.TemporaryDirectory() as d:
            first = one_month(d, 1985, 1, fetcher=lambda _: raw)
            again = one_month(d, 1985, 1, fetcher=lambda _: self.fail("Cache should avoid network"))
            self.assertEqual(first, again)
            self.assertIn('NA', (Path(d) / "ON-1985-01.csv").read_text())
            (Path(d) / "ON-1985-01.csv").write_text("changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                one_month(d, 1985, 1)

    def test_empty_valid_response_is_not_zero_weather(self):
        with tempfile.TemporaryDirectory() as d:
            r = one_month(d, 1985, 1, fetcher=lambda _: weather_csv())
            self.assertEqual(r['status'], 'empty_response')
            self.assertEqual(one_month(d, 1985, 1, fetcher=lambda _: self.fail("Reuse evidence")), r)

    def test_html_and_duplicates_are_not_valid_data(self):
        with self.assertRaises(ValueError):
            validate(b'<html>error</html>', 'ON')
        row = [-78, 45, "Station", "A001", "ON", 1, 0, 2, 0]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate(weather_csv([row, row]), 'ON')

    def test_failed_request_can_be_retried_without_fabricated_csv(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(_):
                raise OSError('network failure')
            self.assertEqual(one_month(d, 1985, 1, fetcher=fail)['status'], 'request_failed')
            self.assertFalse((Path(d) / 'ON-1985-01.csv').exists())
            self.assertEqual(one_month(d, 1985, 1, fetcher=lambda _: weather_csv())['status'], 'empty_response')


try:
    import rasterio
    import numpy as np
    from rasterio.transform import from_origin
    from scripts.download_woodland import crop, plan
except ImportError:
    rasterio = None


@unittest.skipIf(rasterio is None, 'Install optional data dependency group for raster checks')
class WoodlandTests(unittest.TestCase):
    def test_unavailable_years_are_explicit_not_download_urls(self):
        p = plan(2022, 2025)
        self.assertEqual(p[0]['status'], 'available_at_source')
        self.assertTrue(all(r['url'] is None for r in p[1:]))

    def test_native_grid_classes_preserved_and_rgb_rejected(self):
        from rasterio.warp import transform_bounds
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d)/'raw.tif', Path(d)/'crop.tif'
            data = np.full((100,100), 210, dtype='uint8');data[:,50:] = 20
            profile = dict(driver='GTiff',width=100,height=100,count=1,dtype='uint8',crs='EPSG:3978',transform=from_origin(1000000,1000000,30,30),nodata=255)
            with rasterio.open(source,'w',**profile) as r:r.write(data,1)
            bbox = transform_bounds('EPSG:3978','EPSG:4326',1000100,997100,1002900,999900)
            info = crop(source,out,bbox)
            self.assertEqual(set(info['class_pixel_counts']), {'20','210'})
            with rasterio.open(out) as r:self.assertEqual(r.res,(30.,30.));self.assertEqual(r.count,1)
            profile['count']=3
            with rasterio.open(source,'w',**profile) as r:r.write(np.stack([data]*3))
            with self.assertRaisesRegex(ValueError, 'one-band'):
                crop(source,Path(d)/'rgb.tif',bbox)

    def test_nodata_only_is_not_a_valid_crop(self):
        from rasterio.warp import transform_bounds
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'raw.tif'
            with rasterio.open(p,'w',driver='GTiff',width=100,height=100,count=1,dtype='uint8',crs='EPSG:3978',transform=from_origin(1000000,1000000,30,30),nodata=255) as r:r.write(np.full((100,100),255,dtype='uint8'),1)
            bbox=transform_bounds('EPSG:3978','EPSG:4326',1000100,997100,1002900,999900)
            with self.assertRaisesRegex(ValueError,'no classified'):
                crop(p,Path(d)/'out.tif',bbox)
