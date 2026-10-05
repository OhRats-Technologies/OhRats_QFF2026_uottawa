import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from wildfire_lab.final_features import preflight,held_out
from wildfire_lab.group_screen import run


class FinalFeatureTests(unittest.TestCase):
    def fixture(self,root):
        folder=root/'.cache/wildfire/features/historical-woodland/fixture';folder.mkdir(parents=True)
        data=folder/'features.csv';data.write_text('incident_id,year,latitude\ntrain,1988,48\n')
        h=hashlib.sha256(data.read_bytes()).hexdigest()
        archive=root/'data/raw/nfdb-audit/source.zip';archive.parent.mkdir(parents=True);archive.write_bytes(b'archive')
        weather=root/'.cache/wildfire/processed/weather/weather/weather_months.csv';weather.parent.mkdir(parents=True);weather.write_bytes(b'weather')
        (weather.parent/'manifest.json').write_text(json.dumps({'output_sha256':hashlib.sha256(b'weather').hexdigest()}))
        maps=root/'data/raw/woodland';maps.mkdir(parents=True)
        for year in [1984,*range(2018,2023)]:
            (maps/f'woodland-{year}.tif').write_bytes(b'raster')
            (maps/f'woodland-{year}.json').write_text(json.dumps({'crop_sha256':hashlib.sha256(b'raster').hexdigest()}))
        cover=dict(mode='fixed_historical',radius_m=1000,min_classified_fraction=.5,sources=[{'year':1984}])
        protocol=dict(woodland=cover,weather_fingerprint='weather',source_sha256=hashlib.sha256(b'archive').hexdigest())
        (folder/'manifest.json').write_text(json.dumps(dict(protocol=protocol,data_sha256=h)))
        return dict(training_dataset_fingerprint='fixture',training_data_sha256=h,
                    cover_policy=dict(mode='fixed_historical',fixed_year=1984,latest_map_year=2022,radius_m=1000),
                    features=['latitude'],feature_groups={'location':['latitude']})

    def test_preflight_policies_hashes_and_2024_map_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=self.fixture(root)
            _,_,sources=preflight(plan,root)
            self.assertEqual(set(sources['mapped'].values()),{1984})
            plan['cover_policy']['radius_m']=500
            with self.assertRaisesRegex(ValueError,'policies differ'):preflight(plan,root)
            plan['cover_policy'].update(radius_m=1000,mode='previous_year')
            folder=root/'.cache/wildfire/features/historical-woodland/fixture/manifest.json'
            manifest=json.loads(folder.read_text());manifest['protocol']['woodland']['mode']='previous_year';folder.write_text(json.dumps(manifest))
            _,_,sources=preflight(plan,root)
            self.assertEqual(sources['mapped'][2024],2022)
            (root/'data/raw/nfdb-audit/source.zip').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'NFDB'):preflight(plan,root)

    def test_held_out_preserves_weather_and_cover_join_rules(self):
        rows=[dict(incident_id='test',year=2024,date='2024-06-01',latitude=48,longitude=-80,target=1)]
        plan=dict(threshold_ha=10,cover_policy=dict(radius_m=1000))
        manifest=dict(protocol=dict(weather_lags_months=[1,2,3],max_station_distance_km=150))
        sources=dict(archive=Path('fixture.zip'),weather=Path('fixture.csv'),mapped={2024:2022},
                     assets={2022:dict(path=Path('fixture.tif'),sha256='hash')},weather_sha256='weather')
        with patch('wildfire_lab.final_features.incidents',return_value=(rows,{})) as incidents, \
             patch('wildfire_lab.final_features.WeatherIndex') as weather, \
             patch('wildfire_lab.final_features.weather_rows',return_value=(rows,{})) as joined, \
             patch('wildfire_lab.final_features.WoodlandIndex') as woodland:
            woodland.return_value.features.return_value=[dict(cover_water=.5)]
            test,metadata=held_out(plan,manifest,sources)
            incidents.assert_called_once_with(Path('fixture.zip'),start=2019,end=2024,threshold_ha=10)
            joined.assert_called_once_with(rows,weather.return_value,[1,2,3],150)
            woodland.assert_called_once_with(Path('fixture.tif'),2022,1000)
            self.assertEqual(test.cover_age_years.tolist(),[2]);self.assertEqual(metadata['rows'],1)

    def test_year_metrics_reuse_predictions_and_mark_single_class(self):
        train=pd.DataFrame(dict(latitude=range(20),target=[0,1]*10))
        test=pd.DataFrame(dict(latitude=[2,4,12,14],target=[0,1,1,1],year=[2019,2019,2020,2020]))
        rows=run(train,test,dict(feature_groups={'location':['latitude']},report_per_year=True),211)
        for row in rows:
            self.assertEqual(row['metric']['rows'],4)
            self.assertEqual(row['metrics_by_year']['2019']['rows'],2)
            self.assertEqual(row['metrics_by_year']['2020']['status'],'one_class')
