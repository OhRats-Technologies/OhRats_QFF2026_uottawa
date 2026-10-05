"""Prepare 1988–2018 NFDB labels and lagged weather; final-test labels stay sealed."""

import argparse
import hashlib
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.weather_preparation import prepare_weather
from wildfire_lab.nfdb import incidents
from wildfire_lab.weather import WeatherIndex
from wildfire_lab.feature_joins import weather_rows


def build(lags=(2, 3)):
    import pandas as pd

    archive = ROOT / "data/raw/nfdb-audit/source.zip"
    recipe_paths = [
        Path(__file__),
        ROOT / "wildfire_lab/weather_preparation.py",
        ROOT / "wildfire_lab/nfdb.py",
        ROOT / "wildfire_lab/weather.py",
        ROOT / "wildfire_lab/feature_joins.py",
        ROOT / "uv.lock",
    ]
    frozen = [p.read_bytes() for p in recipe_paths]
    recipe_sha256 = {
        str(p.relative_to(ROOT)): hashlib.sha256(raw).hexdigest()
        for p, raw in zip(recipe_paths, frozen)
    }
    recipe_commit = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    )
    weather_path, weather_manifest = prepare_weather(
        ROOT / "configs/wildfires/ontario.json",
        ROOT / "data/raw/weather",
        ROOT / ".cache/wildfire",
    )
    protocol = dict(
        source="NRCan NFDB point snapshot 20260811",
        source_url="https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip",
        source_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        years=[1988, 2018],
        label="agency-reported SIZE_HA >=10 ha, conditional on eligible recorded fire",
        weather_fingerprint=weather_manifest["fingerprint"],
        weather_lags_months=list(lags),
        max_station_distance_km=150,
        woodland="not yet joined; historical weather-only baseline",
        final_test_sealed=True,
    )
    fingerprint = hashlib.sha256(
        json.dumps(protocol, sort_keys=True).encode() + b"".join(frozen)
    ).hexdigest()[:20]
    destination = ROOT / ".cache/wildfire/features/historical-weather" / fingerprint
    if destination.exists():
        manifest = json.loads((destination / "manifest.json").read_text())
        if (
            hashlib.sha256((destination / "features.csv").read_bytes()).hexdigest()
            != manifest["data_sha256"]
        ):
            raise ValueError("Derived cache hash changed")
        return destination, manifest
    rows, excluded = incidents(archive)
    weather = WeatherIndex(weather_path / "weather_months.csv")
    joined, drops = weather_rows(rows, weather, lags)
    if frozen != [p.read_bytes() for p in recipe_paths]:
        raise RuntimeError("Recipe changed during preparation")
    frame = pd.DataFrame(joined).sort_values(["date", "incident_id"])
    destination.mkdir(parents=True)
    frame.to_csv(destination / "features.csv", index=False)
    manifest = dict(
        protocol=protocol,
        fingerprint=fingerprint,
        recipe_sha256=recipe_sha256,
        recipe_commit=recipe_commit,
        created_utc=datetime.now(timezone.utc).isoformat(),
        rows=len(frame),
        rows_by_year=frame.groupby("year").size().to_dict(),
        positive_fraction=float(frame.target.mean()),
        exclusions=excluded,
        join_drops=dict(drops),
        data_sha256=hashlib.sha256(
            (destination / "features.csv").read_bytes()
        ).hexdigest(),
        limitations="Agency-associated dates/sizes, not guaranteed ignition or final burned area. Approximate coordinates and variable source completeness. Unknown publication latency; retrospective classification. Prescribed flags excluded; blank flags are unspecified. Woodland joins pending.",
    )
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return destination, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lags", type=int, nargs="+", default=[2, 3])
    args = parser.parse_args()
    if not args.lags or any(lag not in {1, 2, 3, 4} for lag in args.lags):
        parser.error("Use antecedent monthly lags 1–4")
    path, manifest = build(tuple(sorted(set(args.lags))))
    print(path)
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in [
                    "rows",
                    "rows_by_year",
                    "positive_fraction",
                    "exclusions",
                    "join_drops",
                ]
            },
            indent=2,
        )
    )
