"""Resumable ECCC station-month CSV acquisition; keep unavailable months explicit."""
import argparse
import csv
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "https://climate.weather.gc.ca/prods_servs/cdn_climate_summary_report_e.html"
REQUIRED = {"Long", "Lat", "Stn_Name", "Clim_ID", "Prov_or_Ter", "Tm", "DwTm", "P", "DwP"}


def source_url(year, month, province, fmt="csv"):
    return BASE + "?" + urlencode({"intYear": year, "intMonth": month, "prov": province, "dataFormat": fmt})


def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read()


def validate(raw, province):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("Not an ECCC monthly-summary CSV")
    rows = list(reader)
    ids = set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed CSV row")
        if row["Prov_or_Ter"].strip() != province:
            raise ValueError("Unexpected province")
        ident = row["Clim_ID"].strip()
        if not ident or ident in ids:
            raise ValueError("Missing or duplicate climate identifier")
        ids.add(ident)
    return len(rows)


def one_month(root, year, month, province="ON", fetcher=fetch):
    stem = f"{province}-{year}-{month:02d}"
    path, meta = Path(root) / (stem + ".csv"), Path(root) / (stem + ".json")
    url = source_url(year, month, province)
    if meta.exists():
        old = json.loads(meta.read_text())
        if old.get("status") in {"downloaded", "empty_response"} and path.exists():
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != old["sha256"]:
                raise ValueError(f"Snapshot hash mismatch: {stem}")
            validate(raw, province)
            return old
    if path.exists():
        raise FileExistsError(f"Unmanifested raw file: {path}")
    record = {"year": year, "month": month, "province": province, "url": url,
              "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    try:
        raw = fetcher(url)
        count = validate(raw, province)
        record.update(status="downloaded" if count else "empty_response", rows=count,
                      sha256=hashlib.sha256(raw).hexdigest(), file=path.name)
        # Empty valid responses are evidence too; never manufacture station rows.
        tmp = path.with_suffix(".csv.part")
        tmp.write_bytes(raw)
        tmp.replace(path)
    except (OSError, ValueError, UnicodeError) as exc:
        record.update(status="request_failed", error=str(exc)[:400])
    tmp = meta.with_suffix(".json.part")
    tmp.write_text(json.dumps(record, indent=2) + "\n")
    tmp.replace(meta)
    return record


def download(root, start=1987, end=2024, province="ON", workers=3):
    if not 1 <= workers <= 4 or start > end:
        raise ValueError("Use 1–4 workers and an ordered year range")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    tasks = [(y, m) for y in range(start, end + 1) for m in range(1, 13)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(lambda ym: one_month(root, *ym, province), tasks))
    result = {"start_year": start, "end_year": end, "province": province, "months": records,
              "limitations": "Monthly station observations; basic source QC, revisions possible. Empty/failure is not zero weather."}
    (root / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1987)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--province", choices=["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"], default="ON")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("data/raw/weather"))
    args = parser.parse_args()
    result = download(args.output, args.start_year, args.end_year, args.province, args.workers)
    completed = sum(x["status"] == "downloaded" for x in result["months"])
    print(f"Downloaded/cached {completed}/{len(result['months'])} station-month files; see {args.output / 'manifest.json'} for gaps.")
