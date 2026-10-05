"""One training-only incident example from the operational update feed."""
import csv
import math
from collections import Counter, defaultdict
from datetime import date


def operational_incidents(path, start=2010, end=2018, threshold_ha=10):
    groups = defaultdict(list)
    excluded = Counter()
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if start <= int(row["status_year"]) <= end:
                groups[row["national_fire_id"]].append(row)
    examples = []
    for ident, rows in groups.items():
        rows.sort(key=lambda r: (r["record_start"], int(r["id"])))
        first = rows[0]
        try:
            day = date.fromisoformat(first["situation_report_date"][:10])
            lat, lon = float(first["latitude"]), float(first["longitude"])
            sizes = [float(r["fire_size"]) for r in rows if math.isfinite(float(r["fire_size"])) and float(r["fire_size"]) >= 0]
        except ValueError:
            excluded["invalid_date_location_size"] += 1
            continue
        if not start <= day.year <= end or any(int(r["fire_year"]) != day.year for r in rows):
            excluded["inconsistent_fire_year"] += 1
            continue
        if not sizes or not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            excluded["invalid_date_location_size"] += 1
            continue
        # Positive prescribed codes lack a verified binary crosswalk; exclude them.
        if any(r["fire_was_prescribed"] not in {"-1", "0", ""} for r in rows):
            excluded["prescribed_or_unknown_code"] += 1
            continue
        examples.append(dict(incident_id=ident, date=day.isoformat(), year=day.year,
                             latitude=lat, longitude=lon, target=int(max(sizes) >= threshold_ha)))
    return examples, dict(excluded)
