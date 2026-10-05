"""Build a 2010–2018 conditional reported-size pilot; do not open final-test labels."""
import hashlib
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pipeline import prepare_weather
from wildfire_lab.fire import operational_incidents
from wildfire_lab.weather import WeatherIndex
from wildfire_lab.woodland import WoodlandIndex


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    import pandas as pd
    recipe_paths = [Path(__file__), *(ROOT / p for p in ["wildfire_lab/fire.py", "wildfire_lab/weather.py", "wildfire_lab/woodland.py"])]
    recipe_bytes = [p.read_bytes() for p in recipe_paths]
    sources = [ROOT / "data/wildfires/ontario/reports.csv", ROOT / "data/raw/woodland/woodland-1988.tif"]
    source_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]
    weather_path, weather_manifest = prepare_weather(ROOT / "configs/wildfires/ontario.json", ROOT / "data/raw/weather", ROOT / ".cache/wildfire")
    incidents, excluded = operational_incidents(sources[0])
    cover = WoodlandIndex(sources[1]).features(incidents)
    weather = WeatherIndex(weather_path / "weather_months.csv")
    joined, drops = [], Counter()
    for incident, forest in zip(incidents, cover):
        if forest is None:
            drops["insufficient_woodland_coverage"] += 1
            continue
        lag2, lag3 = weather.query(incident, 2), weather.query(incident, 3)
        if lag2 is None or lag3 is None:
            drops["weather_outside_150km_or_missing_month"] += 1
            continue
        month = int(incident["date"][5:7])
        row = dict(incident, **forest, **lag2[0], **lag3[0],
                   month_sin=math.sin(2*math.pi*month/12), month_cos=math.cos(2*math.pi*month/12),
                   station_lag2=lag2[1]["climate_id"], station_lag3=lag3[1]["climate_id"],
                   weather_distance_lag2=lag2[1]["distance_km"], weather_distance_lag3=lag3[1]["distance_km"])
        joined.append(row)
    protocol = dict(label="peak reported size within 2010–2018 update snapshot >=10 ha, conditional on recorded fire",
                    source="operational feed pilot; earlier NFDB candidate not substituted", years=[2010,2018],
                    source_hashes=source_hashes, weather_fingerprint=weather_manifest["fingerprint"],
                    woodland_year=1988, buffer_radius_m=1000, weather_lags_months=[2,3], max_station_distance_km=150)
    fingerprint = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()+b"".join(recipe_bytes)).hexdigest()[:20]
    if recipe_bytes != [p.read_bytes() for p in recipe_paths]:
        raise RuntimeError("Recipe changed during preparation; do not publish this dataset")
    destination = ROOT / ".cache/wildfire/features/operational-pilot" / fingerprint
    if destination.exists():
        raise FileExistsError("Pilot already prepared; reuse its immutable manifest")
    destination.mkdir(parents=True)
    frame = pd.DataFrame(joined).sort_values(["date","incident_id"])
    frame.to_csv(destination / "features.csv", index=False)
    manifest = dict(protocol=protocol, fingerprint=fingerprint, created_utc=datetime.now(timezone.utc).isoformat(),
                    rows=len(frame), rows_by_year=frame.groupby("year").size().to_dict(),
                    positive_fraction=float(frame.target.mean()), exclusions=excluded, join_drops=dict(drops),
                    data_sha256=hashlib.sha256((destination/"features.csv").read_bytes()).hexdigest(),
                    limitations="Retrospective classification of recorded-size proxy, not ignition forecasting. Approximate locations, reporting gaps, fixed historic cover and unknown publication latency.")
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(destination)
    print(json.dumps({k:manifest[k] for k in ["rows","rows_by_year","positive_fraction","exclusions","join_drops"]},indent=2))
