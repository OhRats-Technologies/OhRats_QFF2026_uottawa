import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from wildfire_lab.weather_preparation import prepare_weather


class WeatherPreparationTests(unittest.TestCase):
    def test_source_integrity_split_and_immutable_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'raw';raw.mkdir();config=root/'config.json'
            config.write_text(json.dumps(dict(start_year=1988,end_year=1989,province='ON',
                train=dict(start_year=1988,end_year=1988),test=dict(start_year=1989,end_year=1989))))
            contents='Clim_ID,Stn_Name,Prov_or_Ter,Long,Lat,Tm,P\nA001,Station,ON,-78,45,NA,0\n'
            digest=hashlib.sha256(contents.encode()).hexdigest()
            for year in (1988,1989):
                for month in range(1,13):
                    stem=raw/f'ON-{year}-{month:02d}'
                    stem.with_suffix('.csv').write_text(contents)
                    stem.with_suffix('.json').write_text(json.dumps(dict(status='downloaded',sha256=digest)))
            destination,manifest=prepare_weather(config,raw,root/'cache')
            output=destination/'weather_months.csv';before=output.stat().st_mtime_ns
            with output.open() as incoming:rows=list(csv.DictReader(incoming))
            self.assertEqual(manifest['rows_by_split'],dict(train=12,test=12,context=0))
            self.assertEqual({r['climate_id'] for r in rows},{'A001'})
            self.assertEqual(rows[0]['mean_temp_c'],'')
            self.assertEqual(rows[0]['total_precip_mm'],'0.0')
            self.assertEqual(rows[12]['split'],'test')
            again,reused=prepare_weather(config,raw,root/'cache')
            self.assertEqual(again,destination);self.assertEqual(reused,manifest)
            self.assertEqual(output.stat().st_mtime_ns,before)
            (raw/'ON-1988-01.csv').write_text(contents+'tampered')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                prepare_weather(config,raw,root/'cache')
            self.assertEqual(output.stat().st_mtime_ns,before)
