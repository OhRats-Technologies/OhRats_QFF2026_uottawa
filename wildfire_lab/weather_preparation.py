"""Typed station-month preparation; raw values and immutable cache versions."""
import calendar
import csv
import hashlib
import io
import json
import math
import tempfile
from datetime import datetime,timezone
from pathlib import Path

FIELDS = {
    "Long": "longitude", "Lat": "latitude", "Tm": "mean_temp_c",
    "Tx": "highest_max_temp_c", "Tn": "lowest_min_temp_c",
    "DwTm": "missing_mean_temp_days", "DwTx": "missing_max_temp_days",
    "DwTn": "missing_min_temp_days", "P": "total_precip_mm",
    "DwP": "missing_precip_days", "Pd": "precip_days_ge_1mm",
    "S": "snowfall_cm", "DwS": "missing_snowfall_days",
    "S_G": "month_end_snow_cm", "HDD": "heating_degree_days", "CDD": "cooling_degree_days",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(raw, name, days, flags):
    if raw is None or raw.strip() in {"", "NA"}:
        return ""
    try:
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError()
    except ValueError:
        flags.append(name + ":invalid_number")
        return ""
    if name.startswith("missing_") and (not 0 <= value <= days or not value.is_integer()):
        flags.append(name + ":suspect_day_count")
    return value


def normalized(row, year, month, split):
    flags = []
    result = dict(climate_id=row["Clim_ID"].strip(), station_name=row["Stn_Name"],
                  province=row["Prov_or_Ter"], month=f"{year}-{month:02d}-01", split=split)
    for source, target in FIELDS.items():
        result[target] = number(row.get(source), target, calendar.monthrange(year, month)[1], flags)
    if result["longitude"] == "" or result["latitude"] == "" or not (-180 <= result["longitude"] <= 180 and -90 <= result["latitude"] <= 90):
        flags.append("invalid_location")
    result["quality_flags"] = ";".join(flags)
    return result


def prepare_weather(config_path, raw_root, cache):
    config_raw = config_path.read_bytes()
    config = json.loads(config_raw)
    inputs = []
    for year in range(config.get("context_start_year", config["start_year"]), config["end_year"] + 1):
        for month in range(1, 13):
            stem = f"{config['province']}-{year}-{month:02d}"
            path = raw_root / (stem + ".csv")
            meta = json.loads((raw_root / (stem + ".json")).read_text())
            digest = sha(path.read_bytes())
            if meta["status"] != "downloaded" or meta["sha256"] != digest:
                raise ValueError(f"Source unavailable or hash mismatch: {stem}")
            inputs.append(dict(year=year, month=month, path=path, sha256=digest))
    fingerprint = sha(json.dumps([sha(config_raw), sha(Path(__file__).read_bytes()), [x["sha256"] for x in inputs]]).encode())[:20]
    destination = cache / "processed/weather" / fingerprint
    if destination.exists():
        manifest = json.loads((destination / "manifest.json").read_text())
        if sha((destination / "weather_months.csv").read_bytes()) != manifest["output_sha256"]:
            raise ValueError("Prepared cache hash mismatch")
        return destination, manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".prepare-") as temp:
        temp = Path(temp)
        output = temp / "weather_months.csv"
        counts = {"train": 0, "test": 0, "context": 0}
        flagged = 0
        with output.open("w", newline="") as f:
            writer = None
            for source in inputs:
                year, month = source["year"], source["month"]
                splits = [s for s in ("train", "test") if config[s]["start_year"] <= year <= config[s]["end_year"]]
                if config.get("context_start_year", config["start_year"]) <= year < config["start_year"]:
                    splits = ["context"]
                if len(splits) != 1:
                    raise ValueError("Each year must have exactly one split")
                raw_bytes = source["path"].read_bytes()
                if sha(raw_bytes) != source["sha256"]:
                    raise ValueError("Source changed during preparation")
                with io.StringIO(raw_bytes.decode("utf-8-sig")) as incoming:
                    seen = set()
                    for raw in csv.DictReader(incoming):
                        row = normalized(raw, year, month, splits[0])
                        if not row["climate_id"] or row["climate_id"] in seen or row["province"] != config["province"]:
                            raise ValueError("Invalid station identity/province")
                        seen.add(row["climate_id"])
                        if writer is None:
                            writer = csv.DictWriter(f, fieldnames=list(row))
                            writer.writeheader()
                        writer.writerow(row)
                        counts[splits[0]] += 1
                        flagged += bool(row["quality_flags"])
        manifest = dict(stage="weather_preparation", fingerprint=fingerprint,
                        config_sha256=sha(config_raw), code_sha256=sha(Path(__file__).read_bytes()),
                        created_utc=datetime.now(timezone.utc).isoformat(), rows_by_split=counts,
                        flagged_rows=flagged, output_sha256=sha(output.read_bytes()),
                        inputs=[dict(file=x["path"].name, sha256=x["sha256"]) for x in inputs],
                        limitations="Station-month preparation only; fire/spatial joins are separate stages. Publication times unresolved. No imputation or fitted preprocessing.")
        (temp / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        # Reserve an immutable cache version without overwriting another process.
        destination.mkdir()
        for path in temp.iterdir():
            path.rename(destination / path.name)
    return destination, manifest
