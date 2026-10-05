"""Freeze the public Ontario agency-reported fire history, with full pagination."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import urlopen

SOURCE = "https://geoserver.cwfif.nrcan.gc.ca/geoserver/ows"
AGENCIES = ("AB", "BC", "MB", "NB", "NL", "NS", "NT", "ON", "PC", "PE", "QC", "SK", "YT")
PAGE_SIZE = 10_000


def page_url(agency, offset):
    if agency not in AGENCIES:
        raise ValueError("Unsupported agency code")
    return SOURCE + "?" + urlencode({
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": "public:cwfif_national_reportedfires", "outputFormat": "csv",
        "CQL_FILTER": f"agency_code='{agency}'", "sortBy": "id A",
        "count": PAGE_SIZE, "startIndex": offset,
    })


def fetch_page(url):
    with urlopen(url, timeout=120) as response:
        return response.read().decode("utf-8-sig")


def download(output, agency="ON", fetch=fetch_page):
    """Publish only after all pages validate; never overwrite an existing snapshot."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Choose a fresh snapshot directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    ids, fire_ids, urls = set(), set(), []
    years, dated = Counter(), set()
    columns = None
    with TemporaryDirectory(prefix=".wildfires-", dir=output.parent) as temp:
        temp = Path(temp)
        raw = temp / "reports.csv"
        with raw.open("w", newline="", encoding="utf-8") as stream:
            for offset in range(0, 10_000_000, PAGE_SIZE):
                url = page_url(agency, offset)
                urls.append(url)
                reader = csv.DictReader(io.StringIO(fetch(url)))
                if not reader.fieldnames or not {"id", "agency_code", "national_fire_id", "status_year", "situation_report_date"}.issubset(reader.fieldnames):
                    raise ValueError("Response is not the expected fire-history CSV")
                if columns is None:
                    columns = reader.fieldnames
                    writer = csv.DictWriter(stream, fieldnames=columns)
                    writer.writeheader()
                elif reader.fieldnames != columns:
                    raise ValueError("CSV schema changed between pages")
                rows = list(reader)
                for row in rows:
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError("Malformed CSV row")
                    ident = row["id"].strip()
                    if not ident or ident in ids:
                        raise ValueError("Missing/repeated update ID; snapshot may have changed during pagination")
                    if row["agency_code"].strip() != agency:
                        raise ValueError("Agency filter was not respected")
                    ids.add(ident)
                    fire_ids.add(row["national_fire_id"])
                    years[row["status_year"]] += 1
                    date = row["situation_report_date"][:10]
                    if date:
                        dated.add((row["status_year"], date))
                    writer.writerow(row)
                if len(rows) < PAGE_SIZE:
                    break
            else:
                raise ValueError("Pagination safety limit reached")
        if not ids:
            raise ValueError("No fire records returned; snapshot not published")
        metadata = {
            "catalogue": "https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/937eb7be-83fd-4b94-a122-9cc0385f3bf7",
            "agency": agency, "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "query_urls": urls, "rows": len(ids), "distinct_fire_ids": len(fire_ids),
            "rows_by_status_year": dict(sorted(years.items())),
            "distinct_report_dates_by_status_year": dict(sorted(Counter(y for y, _ in dated).items())),
            "csv_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            "limitations": "Non-atomic operational update history; not a complete daily grid or a fire-absence label source.",
        }
        (temp / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        # mkdir reserves the destination; concurrent runs cannot replace a snapshot.
        output.mkdir()
        raw.rename(output / raw.name)
        (temp / "metadata.json").rename(output / "metadata.json")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agency", choices=AGENCIES, default="ON")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = download(args.output, args.agency)
    print(f"Saved {result['rows']:,} update records for {result['distinct_fire_ids']:,} fire IDs to {args.output}")
