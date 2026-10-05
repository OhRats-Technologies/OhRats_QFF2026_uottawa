"""Add native buffered woodland context to an immutable feature snapshot."""

import argparse
import hashlib
import json
import sys
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.download_woodland import digest
from wildfire_lab.woodland import WoodlandIndex


def build(parent, fixed_year=1984, radius_m=1000, annual=False):
    import pandas as pd

    start = time.perf_counter()
    parent = parent.resolve()
    manifest = json.loads((parent / "manifest.json").read_text())
    if digest(parent / "features.csv") != manifest["data_sha256"]:
        raise ValueError("Parent snapshot hash changed")
    frame = pd.read_csv(
        parent / "features.csv",
        dtype={f"station_lag{lag}": str for lag in [1, 2, 3, 4]},
    )
    if frame.year.max() > 2018:
        raise ValueError("Discovery join cannot open final-test labels")
    years = sorted(set(frame.year - 1)) if annual else [fixed_year]
    sources = []
    for year in years:
        path = ROOT / "data/raw/woodland" / f"woodland-{year}.tif"
        meta = json.loads(path.with_suffix(".json").read_text())
        if digest(path) != meta["crop_sha256"]:
            raise ValueError("Woodland hash changed")
        sources.append(
            dict(
                year=int(year),
                crop_sha256=meta["crop_sha256"],
                archive_sha256=meta["archive_sha256"],
                local_archive=meta["local_archive"],
            )
        )
    recipes = [Path(__file__), ROOT / "wildfire_lab/woodland.py", ROOT / "uv.lock"]
    frozen = [p.read_bytes() for p in recipes]
    join_recipe_sha256 = {
        str(p.relative_to(ROOT)): hashlib.sha256(raw).hexdigest()
        for p, raw in zip(recipes, frozen)
    }
    join_recipe_commit = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    )
    protocol = dict(
        manifest["protocol"],
        woodland=dict(
            mode="previous_year" if annual else "fixed_historical",
            sources=sources,
            radius_m=radius_m,
            min_classified_fraction=0.5,
        ),
        parent_fingerprint=manifest["fingerprint"],
    )
    fingerprint = hashlib.sha256(
        json.dumps(protocol, sort_keys=True).encode() + b"".join(frozen)
    ).hexdigest()[:20]
    destination = ROOT / ".cache/wildfire/features/historical-woodland" / fingerprint
    if destination.exists():
        stored = json.loads((destination / "manifest.json").read_text())
        if digest(destination / "features.csv") != stored["data_sha256"]:
            raise ValueError("Derived cache changed")
        return destination, stored
    joined = []
    drops = Counter()
    for year in years:
        selected = frame.loc[frame.year == year + 1] if annual else frame
        points = selected.to_dict("records")
        cover = WoodlandIndex(
            ROOT / "data/raw/woodland" / f"woodland-{year}.tif", int(year), radius_m
        ).features(points)
        for point, forest in zip(points, cover):
            if forest is None:
                drops["insufficient_woodland_coverage"] += 1
                continue
            joined.append(
                dict(
                    point,
                    **forest,
                    cover_year=int(year),
                    cover_age_years=int(point["year"] - year),
                )
            )
    if frozen != [p.read_bytes() for p in recipes]:
        raise RuntimeError("Recipe changed during join")
    output = pd.DataFrame(joined).sort_values(["date", "incident_id"])
    destination.mkdir(parents=True)
    output.to_csv(destination / "features.csv", index=False)
    result = dict(
        manifest,
        join_recipe_sha256=join_recipe_sha256,
        join_recipe_commit=join_recipe_commit,
        protocol=protocol,
        fingerprint=fingerprint,
        created_utc=datetime.now(timezone.utc).isoformat(),
        rows=len(output),
        rows_by_year=output.groupby("year").size().to_dict(),
        positive_fraction=float(output.target.mean()),
        woodland_join_drops=dict(drops),
        center_water_rows=int(output.cover_center_water.sum()),
        data_sha256=digest(destination / "features.csv"),
        seconds=time.perf_counter() - start,
        limitations=manifest["limitations"]
        + " Native cover context now joined. Categories are not tree density; point coordinates are approximate. Center-water flags do not prove a fire burned water. Previous/fixed mapped year does not certify historical publication availability.",
    )
    (destination / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return destination, result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--fixed-year", type=int, default=1984)
    parser.add_argument("--radius-m", type=int, default=1000)
    parser.add_argument("--annual", action="store_true")
    args = parser.parse_args()
    path, result = build(args.dataset, args.fixed_year, args.radius_m, args.annual)
    print(path)
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "rows",
                    "positive_fraction",
                    "woodland_join_drops",
                    "center_water_rows",
                    "seconds",
                ]
            },
            indent=2,
        )
    )
