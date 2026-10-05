"""Compare static and annual woodland on exactly the same historical incidents."""
import argparse
import hashlib
import io
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COVER=['cover_conifer','cover_broadleaf','cover_mixed','cover_water']


def read(parent):
    import pandas as pd
    manifest=json.loads((parent/'manifest.json').read_text())
    raw=(parent/'features.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['data_sha256']:raise ValueError('Parent hash changed')
    frame=pd.read_csv(io.BytesIO(raw),dtype={f'station_lag{lag}':str for lag in [1,2,3,4]})
    if frame.year.max()>2018 or frame.incident_id.duplicated().any():raise ValueError('Use unique training-window incidents')
    return frame,manifest


def build(annual,static):
    a,am=read(annual);s,sm=read(static)
    if am['protocol']['woodland']['mode']!='previous_year' or sm['protocol']['woodland']['mode']!='fixed_historical':
        raise ValueError('Expected annual previous-year and static context parents')
    if am['protocol']['parent_fingerprint']!=sm['protocol']['parent_fingerprint']:
        raise ValueError('Context parents must share the same underlying incidents/weather')
    protocol=dict(am['protocol'],context_comparison=dict(annual_fingerprint=am['fingerprint'],static_fingerprint=sm['fingerprint'],static_woodland=sm['protocol']['woodland']))
    recipe=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    fingerprint=hashlib.sha256(json.dumps([protocol,recipe,am['data_sha256'],sm['data_sha256']],sort_keys=True).encode()).hexdigest()[:20]
    destination=ROOT/'.cache/wildfire/features/historical-context-comparison'/fingerprint
    if destination.exists():
        _,stored=read(destination);return destination,stored
    identity=['date','year','latitude','longitude','target']
    matched=a.merge(s[['incident_id',*identity,*COVER]],on='incident_id',suffixes=('','_static'),validate='one_to_one')
    for column in identity:
        if not matched[column].equals(matched[column+'_static']):raise ValueError('Conflicting incident fields: '+column)
    matched=matched.drop(columns=[c+'_static' for c in identity]).rename(columns={c+'_static':'static_'+c for c in COVER})
    matched=matched.sort_values(['date','incident_id'])
    destination.mkdir(parents=True);matched.to_csv(destination/'features.csv',index=False)
    result=dict(am,protocol=protocol,fingerprint=fingerprint,created_utc=datetime.now(timezone.utc).isoformat(),
                rows=len(matched),rows_by_year=matched.groupby('year').size().to_dict(),positive_fraction=float(matched.target.mean()),
                parent_rows=dict(annual=len(a),static=len(s)),excluded_by_intersection=dict(annual=len(a)-len(matched),static=len(s)-len(matched)),
                code_sha256=recipe,data_sha256=hashlib.sha256((destination/'features.csv').read_bytes()).hexdigest(),
                limitations='Identical-incident static versus previous-year mapped-cover context. Dates/sizes are agency-associated. Native classes are retrospective; map-year lag does not certify historical availability or freedom from temporal smoothing. No final-test performance opened.')
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return destination,result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annual',type=Path,required=True)
    parser.add_argument('--static',type=Path,required=True)
    args=parser.parse_args();path,result=build(args.annual.resolve(),args.static.resolve())
    print(path);print(json.dumps({k:result[k] for k in ['rows','parent_rows','excluded_by_intersection']},indent=2))
