import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from scripts.match_woodland_contexts import build


class ContextMatchingTests(unittest.TestCase):
    def test_common_incidents_and_conflicting_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);parents=[]
            for mode,ids in [('previous_year',['a','b']),('fixed_historical',['b','c'])]:
                path=root/mode;path.mkdir();parents.append(path)
                frame=pd.DataFrame(dict(incident_id=ids,date=['2010-05-01']*2,year=[2010]*2,latitude=[45.]*2,longitude=[-80.]*2,target=[1]*2,cover_conifer=[.5]*2,cover_broadleaf=[.2]*2,cover_mixed=[.1]*2,cover_water=[.2]*2))
                frame.to_csv(path/'features.csv',index=False)
                manifest=dict(protocol={'parent_fingerprint':'same-weather-incidents','woodland':{'mode':mode}},fingerprint=mode,data_sha256=hashlib.sha256((path/'features.csv').read_bytes()).hexdigest())
                (path/'manifest.json').write_text(json.dumps(manifest))
            with patch('scripts.match_woodland_contexts.ROOT',root):
                destination,meta=build(*parents)
                result=pd.read_csv(destination/'features.csv')
                self.assertEqual(result.incident_id.tolist(),['b'])
                self.assertEqual(meta['excluded_by_intersection'],{'annual':1,'static':1})
                self.assertIn('static_cover_water',result)
                changed=pd.read_csv(parents[1]/'features.csv');changed.loc[changed.incident_id=='b','target']=0
                changed.to_csv(parents[1]/'features.csv',index=False)
                manifest=json.loads((parents[1]/'manifest.json').read_text());manifest['data_sha256']=hashlib.sha256((parents[1]/'features.csv').read_bytes()).hexdigest()
                (parents[1]/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError,'Conflicting incident'):build(*parents)
