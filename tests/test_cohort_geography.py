import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from wildfire_lab.label_quality import geographic_retention

SPEC=importlib.util.spec_from_file_location('cohort_geography',Path(__file__).parents[1]/'scripts/audit_cohort_geography.py')
AUDIT=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(AUDIT)


class CohortGeographyTests(unittest.TestCase):
    def setUp(self):
        self.source={key:dict(incident_id=key,year=1988 if key!='d' else 1989,latitude=lat,
            longitude=-80.,target=target) for key,lat,target in [('a',44.,0),('b',45.,1),('c',51.,1),('d',90.,0)]}

    def test_band_boundaries_last_edge_and_denominators(self):
        retained={key:self.source[key] for key in ['a','b']}
        result=geographic_retention(self.source,retained,[-90,45,51,90])
        self.assertEqual(result['before']['median_latitude'],48.)
        self.assertEqual(result['retained']['median_latitude'],44.5)
        self.assertEqual(result['by_target']['1']['excluded_fraction'],.5)
        self.assertEqual(result['latitude_bins'][1]['by_target']['1']['retained_rows'],1)
        self.assertEqual(result['latitude_bins'][2]['by_target']['0']['excluded_rows'],1)
        self.assertTrue(result['latitude_bins'][2]['upper_inclusive'])
        self.assertIsNone(result['latitude_bins'][0]['by_target']['1']['excluded_fraction'])

    def test_invalid_domain_and_changed_records_are_rejected(self):
        for after,edges in [({'unknown':self.source['a']},[-90,90]),
            ({'a':dict(self.source['a'],latitude=45.)},[-90,90]),
            ({'a':dict(self.source['a'],target=1)},[-90,90]),({},[90,-90]),({},[45,90])]:
            with self.subTest(after=after,edges=edges),self.assertRaises(ValueError):
                geographic_retention(self.source,after,edges)
        with self.assertRaises(ValueError):
            geographic_retention({'a':dict(self.source['a'],latitude=float('nan'))},{},[-90,90])

    def fixture(self,root):
        archive=root/'source.zip';archive.write_bytes(b'archive fixture')
        recipe=dict(agency='ON',years=[1988,1989],target_threshold_ha='10',source_archive='source.zip',
            source_sha256=AUDIT.sha(archive),cohorts={})
        for name,keys in [('weather_matched',['a','b','d']),('fixed_cover_matched',['a','b'])]:
            folder=root/name;folder.mkdir();table=folder/'features.csv'
            with table.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=['incident_id','year','latitude','longitude','target']);writer.writeheader()
                writer.writerows(self.source[key] for key in keys)
            digest=AUDIT.sha(table);recipe['cohorts'][name]=dict(dataset=name,sha256=digest)
            (folder/'manifest.json').write_text(json.dumps(dict(rows=len(keys),data_sha256=digest,
                protocol=dict(years=recipe['years'],source_sha256=recipe['source_sha256']))))
        def counts(before,retained,excluded):return dict(before_rows=before,retained_rows=retained,excluded_rows=excluded)
        evidence=dict(retention=dict(weather={'0':counts(2,2,0),'1':counts(2,1,1)},
                                     woodland={'0':counts(2,1,1),'1':counts(1,1,0)}))
        parent=root/'parent.json';parent.write_text(json.dumps(recipe));summary=root/'summary.json';summary.write_text(json.dumps(evidence))
        plan=dict(status='frozen_training_only_source_audit',parent_config='parent.json',parent_config_sha256=AUDIT.sha(parent),
            parent_evidence='summary.json',parent_evidence_sha256=AUDIT.sha(summary),latitude_edges=[-90,45,51,90],max_training_year=2018)
        config=root/'plan.json';config.write_text(json.dumps(plan))
        for name in ['scripts/audit_cohort_geography.py','wildfire_lab/label_quality.py','wildfire_lab/nfdb.py']:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('disposable recipe fixture')
        return config,recipe,plan

    def test_collector_reproduces_counts_and_rejects_coordinate_or_year_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config,recipe,plan=self.fixture(root)
            with patch.object(AUDIT,'incidents',return_value=(list(self.source.values()),{})),patch.object(AUDIT.subprocess,'check_output',return_value='fixture-commit'):
                result=AUDIT.collect(root,config)
                self.assertEqual(result['stages']['weather']['excluded']['rows'],1)
                self.assertEqual(result['stages']['woodland']['excluded']['positive_rows'],0)
                self.assertFalse(result['final_test_access'])
                table=root/'weather_matched/features.csv';table.write_text(table.read_text().replace('44.0','44.01'))
                recipe['cohorts']['weather_matched']['sha256']=AUDIT.sha(table)
                manifest=root/'weather_matched/manifest.json';value=json.loads(manifest.read_text());value['data_sha256']=AUDIT.sha(table);manifest.write_text(json.dumps(value))
                (root/'parent.json').write_text(json.dumps(recipe));plan['parent_config_sha256']=AUDIT.sha(root/'parent.json');config.write_text(json.dumps(plan))
                with self.assertRaisesRegex(ValueError,'coordinate'):AUDIT.collect(root,config)
                recipe['years']=[1988,2019];(root/'parent.json').write_text(json.dumps(recipe))
                plan['parent_config_sha256']=AUDIT.sha(root/'parent.json');config.write_text(json.dumps(plan))
                with self.assertRaisesRegex(ValueError,'Training-period'):AUDIT.collect(root,config)
