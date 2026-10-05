"""Trace joined feature missingness, station distance and native cover flags."""
import argparse
import hashlib
import json
import sys
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.weather import month_lag


def audit(dataset,coordinates_only=False):
    import pandas as pd
    manifest=json.loads((dataset/'manifest.json').read_text())
    raw=(dataset/'features.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['data_sha256']:raise ValueError('Feature hash changed')
    import io
    frame=pd.read_csv(io.BytesIO(raw),usecols=['incident_id','year','latitude','longitude'] if coordinates_only else None,
                      dtype={f'station_lag{lag}':str for lag in [1,2,3,4]})
    if frame.year.max()>2018:raise ValueError('Discovery audit requires training features')
    if coordinates_only:
        from wildfire_lab.coordinate_quality import audit as coordinate_audit,datum_check
        plan_path=ROOT/'experiments/seasonal_baseline.json';plan=json.loads(plan_path.read_text())
        return dict(status='audited_training_coordinate_geometry',created_utc=datetime.now(timezone.utc).isoformat(),
            dataset_sha256=manifest['data_sha256'],dataset_manifest_sha256=hashlib.sha256((dataset/'manifest.json').read_bytes()).hexdigest(),
            code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            audit_recipe_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                ['scripts/audit_feature_quality.py','wildfire_lab/coordinate_quality.py','wildfire_lab/spatial.py','wildfire_lab/evaluation.py']},
            fold_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
            final_test_access=False,training_period_only=True,geometry=coordinate_audit(frame,plan['folds'],tuple(plan['train_years'])),
            datum_sensitivity=datum_check(frame,ROOT/'data/raw/nfdb-audit/source.zip',manifest['protocol']['source_sha256']))
    weather=ROOT/'.cache/wildfire/processed/weather'/manifest['protocol']['weather_fingerprint']
    meta=json.loads((weather/'manifest.json').read_text());raw_weather=(weather/'weather_months.csv').read_bytes()
    if hashlib.sha256(raw_weather).hexdigest()!=meta['output_sha256']:raise ValueError('Weather hash changed')
    source=pd.read_csv(io.BytesIO(raw_weather),dtype={'climate_id':str}).set_index(['month','climate_id'])
    if not source.index.is_unique:raise ValueError('Duplicate station-month source keys')
    result=dict(dataset_sha256=manifest['data_sha256'],weather_sha256=meta['output_sha256'],
                audit_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=len(frame),
                final_test_access=False,training_period_only=True,lags={},limitations='Training joins only. Missing-day flags describe source coverage; they do not certify measurement accuracy or availability. No quality-filtered model is evaluated here.')
    for lag in manifest['protocol']['weather_lags_months']:
        keys=pd.MultiIndex.from_arrays([frame.date.map(lambda day:month_lag(day,lag)),frame[f'station_lag{lag}']])
        joined=source.reindex(keys)
        if joined.province.isna().any():raise ValueError('Untraceable station-month join')
        fields=[c for c in frame if c.startswith(f'lag{lag}_')]
        distance=frame[f'weather_distance_lag{lag}']
        result['lags'][str(lag)]=dict(missing_measurements={c:int(frame[c].isna().sum()) for c in fields},
            distance_km={str(q):float(distance.quantile(q)) for q in [.5,.9,.99]},
            rows_with_source_quality_flags=int(joined.quality_flags.notna().sum()),
            rows_with_missing_days={c:int(joined[c].gt(0).sum()) for c in ['missing_mean_temp_days','missing_precip_days','missing_snowfall_days']},
            unknown_missing_day_counts={c:int(joined[c].isna().sum()) for c in ['missing_mean_temp_days','missing_precip_days','missing_snowfall_days']})
    if 'cover_center_class' in frame:
        result['woodland']=dict(center_class_counts=frame.cover_center_class.value_counts().to_dict(),
            unknown_centers=int(frame.cover_center_class.isin([0,255]).sum()),
            valid_fraction_quantiles={str(q):float(frame.cover_valid_fraction.quantile(q)) for q in [0,.5,.9]},
            mapped_water_centers=int(frame.cover_center_water.sum()),radius_m=manifest['protocol']['woodland']['radius_m'])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--coordinates-only',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=audit(args.dataset.resolve(),args.coordinates_only)
    output=args.output or ROOT/'docs/data'/('coordinate_quality.json' if args.coordinates_only else 'feature_quality.json')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['geometry']['summary'] if args.coordinates_only else result,indent=2))
