"""Acquire and audit historical point records as a candidate source."""
import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.nfdb import audit

URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip"


def acquire(path):
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            with urlopen(URL, timeout=120) as response:
                count = 0
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > 100 * 1024**2:
                        raise ValueError("Unexpected source size")
                    stream.write(chunk)
            stream.close()
            temp.rename(path)
        finally:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/nfdb-audit/source.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/nfdb_audit.json")
    args = parser.parse_args()
    acquire(args.archive)
    result = audit(args.archive)
    result.update(source_url=URL, audited_utc=datetime.now(timezone.utc).isoformat())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("total_agency_rows", "duplicate_identity_groups", "issues")}, indent=2))
