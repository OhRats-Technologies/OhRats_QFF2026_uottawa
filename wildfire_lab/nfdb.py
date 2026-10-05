"""Read and audit the NRCan NFDB point archive without inventing date semantics."""
import csv
import hashlib
import io
import math
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path


def records(archive):
    with zipfile.ZipFile(archive) as z:
        name, = [n for n in z.namelist() if n.startswith("NFDB_point_") and n.endswith(".txt")]
        with z.open(name) as stream:
            yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))


def numeric(raw):
    try:
        value = float(raw)
        return value if math.isfinite(value) and value != -999 else None
    except (TypeError, ValueError):
        return None


def agency_date(row):
    try:
        return date(int(row["YEAR"]), int(row["MONTH"]), int(row["DAY"]))
    except (ValueError, TypeError):
        return None


def flags(row):
    issues = []
    day = agency_date(row)
    if day is None:
        issues.append("invalid_agency_date")
    elif row["REP_DATE"].strip() and row["REP_DATE"][:10] != day.isoformat():
        issues.append("agency_date_disagrees_with_rep_date")
    lat, lon = numeric(row["LATITUDE"]), numeric(row["LONGITUDE"])
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        issues.append("invalid_location")
    size = numeric(row["SIZE_HA"])
    if size is None or size < 0:
        issues.append("unknown_or_negative_reported_size")
    if row["PRESCRIBED"].strip() or row["FIRE_TYPE"].strip() == "PB":
        issues.append("prescribed_or_unspecified_prescribed_code")
    return issues


def audit(archive, agency="ON", start=1988, end=2024):
    annual, issues, causes = {}, Counter(), Counter()
    ids = Counter(row["NFDBFIREID"] for row in records(archive) if row["SRC_AGENCY"] == agency)
    total = 0
    for row in records(archive):
        if row["SRC_AGENCY"] != agency:
            continue
        total += 1
        try:
            year = int(row["YEAR"])
        except ValueError:
            continue
        if not start <= year <= end:
            continue
        counts = annual.setdefault(str(year), Counter())
        counts["rows"] += 1
        found = flags(row)
        if ids[row["NFDBFIREID"]] > 1:
            found.append("identity_collision_quarantined")
        issues.update(found)
        counts["valid_date_location_size_nonprescribed"] += not found
        counts.update(found)
        causes[row["CAUSE"].strip() or "unspecified"] += 1
    return dict(agency=agency, requested_years=[start, end], total_agency_rows=total,
                annual=dict(sorted(annual.items())), issues=dict(issues),
                duplicate_identity_groups=sum(n > 1 for n in ids.values()),
                causes=dict(causes), archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
                semantics="Agency-associated fire date and reported size; ignition time and final size are not guaranteed.",
                limitations="Approximate locations, variable agency/year completeness; audit candidate, not an automatically selected replacement.")


def incidents(archive, agency="ON", start=1988, end=2018, threshold_ha=10):
    """Select historical incident labels without using final-test outcomes."""
    ids = Counter(row["NFDBFIREID"] for row in records(archive) if row["SRC_AGENCY"] == agency)
    accepted, excluded = [], Counter()
    for row in records(archive):
        if row["SRC_AGENCY"] != agency or not start <= int(row["YEAR"]) <= end:
            continue
        found = flags(row)
        if ids[row["NFDBFIREID"]] > 1:
            found.append("identity_collision_quarantined")
        if found:
            excluded.update(found)
            continue
        accepted.append(dict(incident_id=row["NFDBFIREID"], date=agency_date(row).isoformat(), year=int(row["YEAR"]),
                             latitude=numeric(row["LATITUDE"]), longitude=numeric(row["LONGITUDE"]),
                             target=int(numeric(row["SIZE_HA"]) >= threshold_ha)))
    return accepted, dict(excluded)
