"""Verified source preflight and held-out features for the gated final runner."""
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import pandas as pd
from wildfire_lab.feature_joins import weather_rows
from wildfire_lab.nfdb import incidents
from wildfire_lab.weather import WeatherIndex
from wildfire_lab.woodland import WoodlandIndex


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def preflight(plan,root):
    paths=list((root/'.cache/wildfire/features').glob('*/'+plan['training_dataset_fingerprint']+'/manifest.json'))
    path,=paths;manifest=json.loads(path.read_text());raw=path.with_name('features.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=plan['training_data_sha256'] or manifest['data_sha256']!=plan['training_data_sha256']:
        raise ValueError('Training input differs from frozen final plan')
    train=pd.read_csv(io.BytesIO(raw))
    if train.year.min()<1988 or train.year.max()>2018 or train.incident_id.duplicated().any():raise ValueError('Training window/identity mismatch')
    policy=plan['cover_policy'];cover=manifest['protocol']['woodland']
    if cover['mode']!=policy['mode'] or cover['radius_m']!=policy['radius_m'] or cover['min_classified_fraction']!=.5:
        raise ValueError('Train/test cover policies differ')
    if policy['mode']=='fixed_historical' and [s['year'] for s in cover['sources']]!=[policy['fixed_year']]:
        raise ValueError('Fixed training map differs from final policy')
    columns=set(plan['features'])|{c for group in plan['feature_groups'].values() for c in group}
    if not columns.issubset(train.columns):raise ValueError('Frozen feature columns absent from training input')
    weather=root/'.cache/wildfire/processed/weather'/manifest['protocol']['weather_fingerprint']/'weather_months.csv'
    wm=json.loads(weather.with_name('manifest.json').read_text())
    if digest(weather)!=wm['output_sha256']:raise ValueError('Weather snapshot changed')
    archive=root/'data/raw/nfdb-audit/source.zip'
    if digest(archive)!=manifest['protocol']['source_sha256']:raise ValueError('NFDB snapshot changed')
    years=range(2019,2025)
    mapped={year:policy['fixed_year'] if policy['mode']=='fixed_historical' else min(year-1,policy['latest_map_year']) for year in years}
    assets={}
    for year in sorted(set(mapped.values())):
        raster=root/'data/raw/woodland'/f'woodland-{year}.tif';meta=json.loads(raster.with_suffix('.json').read_text())
        if digest(raster)!=meta['crop_sha256']:raise ValueError('Woodland asset changed')
        assets[year]=dict(path=raster,sha256=meta['crop_sha256'])
    return train,manifest,dict(weather=weather,weather_sha256=wm['output_sha256'],archive=archive,mapped=mapped,assets=assets)


def held_out(plan,manifest,sources):
    rows,excluded=incidents(sources['archive'],start=2019,end=2024,threshold_ha=plan['threshold_ha'])
    index=WeatherIndex(sources['weather'],latest_year=2024)
    joined,drops=weather_rows(rows,index,manifest['protocol']['weather_lags_months'],manifest['protocol']['max_station_distance_km'])
    frame=pd.DataFrame(joined);output=[];cover_drops=Counter()
    for year,map_year in sources['mapped'].items():
        points=frame.loc[frame.year.eq(year)].to_dict('records')
        if not points:continue
        cover=WoodlandIndex(sources['assets'][map_year]['path'],map_year,plan['cover_policy']['radius_m']).features(points)
        for point,context in zip(points,cover):
            if context is None:cover_drops['insufficient_woodland_coverage']+=1;continue
            output.append(dict(point,**context,cover_year=map_year,cover_age_years=year-map_year))
    result=pd.DataFrame(output).sort_values(['date','incident_id'])
    return result,dict(rows=len(result),rows_by_year=result.groupby('year').size().to_dict(),exclusions=excluded,
        weather_join_drops=drops,woodland_join_drops=dict(cover_drops),mapped_year_by_test_year=sources['mapped'],
        woodland_sha256={year:asset['sha256'] for year,asset in sources['assets'].items()},weather_sha256=sources['weather_sha256'])
