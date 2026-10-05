"""Audit requested year splits using local hashed downloads; no network access."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

FIRE_URL = "https://api.cwfif.nrcan.gc.ca/reported-fire-stats/docs#/Fire%20Stats%20for%20a%20Given%20Day/get_fire_list_fire_list_get"
WOOD_URL = "https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d"
NFDB_URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip"
WEATHER_URL = "https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_e.html"


def split_year(year, config):
    matches = [s for s in ("train", "test") if config[s]["start_year"] <= year <= config[s]["end_year"]]
    if len(matches) != 1:
        raise ValueError("Each requested year must belong to exactly one split")
    return matches[0]


def verified(path, expected):
    if not path.exists():
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"Hash mismatch: {path.name}")
    return True


def audit(config, root):
    rows = []
    reports = root / "wildfires/ontario/reports.csv"
    fire_rows, report_dates, identities = {}, {}, {}
    if reports.exists():
        metadata = json.loads(reports.with_name("metadata.json").read_text())
        verified(reports, metadata["csv_sha256"])
        with reports.open(newline="") as f:
            for record in csv.DictReader(f):
                year = int(record["status_year"])
                fire_rows[year] = fire_rows.get(year, 0) + 1
                report_dates.setdefault(year, set()).add(record["situation_report_date"][:10])
                identities.setdefault(year, set()).add(record["national_fire_id"])
    nfdb = {}
    archive = root / "raw/nfdb-audit/source.zip"
    if archive.exists():
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from wildfire_lab.nfdb import audit as audit_nfdb
        nfdb = audit_nfdb(archive)["annual"]
    for year in range(config["start_year"], config["end_year"] + 1):
        row = dict(year=year, split=split_year(year, config), weather_months_downloaded=0,
                   nfdb_incident_rows=nfdb.get(str(year), {}).get("rows", ""),
                   nfdb_eligible_before_weather=nfdb.get(str(year), {}).get("valid_date_location_size_nonprescribed", ""),
                   fire_update_rows=fire_rows.get(year, ""), distinct_fire_ids=len(identities[year]) if year in identities else "",
                   distinct_report_dates=len(report_dates[year]) if year in report_dates else "",
                   woodland_status="not_downloaded" if 1984 <= year <= 2022 else "outside_product_years",
                   individual_update_note="operational updates in snapshot; completeness unknown" if year in fire_rows else "no operational updates in snapshot; NFDB incidents reported separately; not no-fire evidence",
                   weather_url=WEATHER_URL, fire_url=FIRE_URL, historical_incident_url=NFDB_URL, woodland_url=WOOD_URL)
        for month in range(1, 13):
            stem = root / "raw/weather" / f"ON-{year}-{month:02d}"
            if stem.with_suffix(".json").exists():
                meta = json.loads(stem.with_suffix(".json").read_text())
                if meta["status"] == "downloaded" and verified(stem.with_suffix(".csv"), meta["sha256"]):
                    row["weather_months_downloaded"] += 1
        meta = root / "raw/woodland" / f"woodland-{year}.json"
        if meta.exists():
            info = json.loads(meta.read_text())
            if verified(meta.with_suffix(".tif"), info["crop_sha256"]):
                row["woodland_status"] = "downloaded"
        rows.append(row)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/wildfires/ontario.json"))
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("docs/data/coverage.csv"))
    args = parser.parse_args()
    rows = audit(json.loads(args.config.read_text()), args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Audited {len(rows)} years: {sum(r['weather_months_downloaded'] for r in rows)} weather months, {sum(bool(r['fire_update_rows']) for r in rows)} years with detailed fire updates, {sum(r['woodland_status']=='downloaded' for r in rows)} woodland crops.")
