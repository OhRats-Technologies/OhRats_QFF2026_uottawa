"""Crop native annual woodland classes; one national archive in temporary storage."""
import argparse
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

CLASSES = {0, 20, 31, 32, 33, 40, 50, 80, 81, 100, 210, 220, 230, 255}
CATALOGUE = "https://open.canada.ca/data/en/dataset/2785c103-9c2d-429b-9f3d-89f5cd9ea94d"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def plan(start, end):
    if start > end:
        raise ValueError("Start year must precede end year")
    return [{"year": year, "status": "available_at_source" if 1984 <= year <= 2022 else "outside_product_years",
             "url": f"https://opendata.nfis.org/downloads/forest_change/CA_forest_VLCE2_{year}.zip" if 1984 <= year <= 2022 else None,
             "evidence_url": CATALOGUE} for year in range(start, end + 1)]


def stream_archive(url, target, max_bytes):
    h, count = hashlib.sha256(), 0
    with urlopen(url, timeout=120) as response, Path(target).open("wb") as stream:
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise ValueError("Archive exceeds configured download budget")
        first = True
        while chunk := response.read(1024 * 1024):
            if first and not chunk.startswith(b"PK"):
                raise ValueError("Source returned a non-ZIP response")
            first = False
            count += len(chunk)
            if count > max_bytes:
                raise ValueError("Archive exceeds configured download budget")
            stream.write(chunk)
            h.update(chunk)
    return h.hexdigest(), count


def crop(source, target, bbox):
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Expected west,south,east,north in geographic degrees")
    with rasterio.open(source) as src:
        if src.crs != rasterio.crs.CRS.from_epsg(3978) or src.count != 1 or src.res != (30., 30.) or src.dtypes != ("uint8",):
            raise ValueError("Expected native one-band 30 m EPSG:3978 uint8 woodland raster")
        bounds = transform_bounds("EPSG:4326", src.crs, *bbox, densify_pts=21)
        w = from_bounds(*bounds, transform=src.transform)
        left, top = math.floor(w.col_off), math.floor(w.row_off)
        right, bottom = math.ceil(w.col_off + w.width), math.ceil(w.row_off + w.height)
        w = Window(left, top, right-left, bottom-top).intersection(Window(0, 0, src.width, src.height))
        profile = src.profile.copy()
        profile.update(driver="GTiff", width=int(w.width), height=int(w.height), transform=src.window_transform(w),
                       tiled=True, blockxsize=256, blockysize=256, compress="deflate", nodata=255, BIGTIFF="IF_SAFER")
        counts = {}
        with rasterio.open(target, "w", **profile) as dst:
            for _, block in dst.block_windows(1):
                raw = src.read(1, window=Window(w.col_off+block.col_off, w.row_off+block.row_off, block.width, block.height))
                import numpy as np
                codes, n = np.unique(raw, return_counts=True)
                if not set(map(int, codes)).issubset(CLASSES):
                    raise ValueError("Unexpected native class values; refuse rendered RGB maps")
                for code, count in zip(codes, n):
                    counts[str(int(code))] = counts.get(str(int(code)), 0) + int(count)
                dst.write(raw, 1, window=block)
        if not sum(v for k, v in counts.items() if int(k) not in {0, 255}):
            raise ValueError("Requested crop has no classified pixels")
        return {"requested_bbox_wgs84": bbox, "source_window": [w.col_off, w.row_off, w.width, w.height],
                "crs": str(src.crs), "resolution_m": list(src.res), "class_pixel_counts": counts,
                "limitations": "Bounding rectangle, not province boundary. Native classes retained; 0 unclassified and 255 nodata."}


def download_year(year, output, bbox, max_gib=2.5, local_archive=None):
    if max_gib <= 0:
        raise ValueError("Archive budget must be positive")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    path, meta = output / f"woodland-{year}.tif", output / f"woodland-{year}.json"
    url = plan(year, year)[0]["url"]
    if not url:
        return {"year": year, "status": "outside_product_years", "evidence_url": CATALOGUE}
    if meta.exists() and path.exists():
        prior = json.loads(meta.read_text())
        if prior["requested_bbox_wgs84"] != list(bbox) or prior["crop_sha256"] != digest(path):
            raise ValueError("Existing crop hash/region differs; choose another output directory")
        return prior
    if path.exists() or meta.exists():
        raise FileExistsError("Incomplete/unmanifested crop; preserve it and choose another output directory")
    if shutil.disk_usage(output).free < (max_gib + 4) * 1024**3:
        raise OSError("Insufficient free disk for temporary national ZIP and TIFF")
    # Per-year temporary storage is removed after the native regional crop is saved.
    with tempfile.TemporaryDirectory(prefix=".woodland-", dir=output) as temp:
        temp = Path(temp)
        if local_archive:
            archive = Path(local_archive)
            source_hash, size = digest(archive), archive.stat().st_size
        else:
            archive = temp / "source.zip"
            source_hash, size = stream_archive(url, archive, int(max_gib * 1024**3))
        with zipfile.ZipFile(archive) as z:
            expected = f"CA_forest_VLCE2_{year}.tif"
            matches = [i for i in z.infolist() if Path(i.filename).name == expected]
            if len(matches) != 1:
                raise ValueError("Archive does not contain exactly the requested year's raster")
            if matches[0].file_size > 4 * 1024**3:
                raise ValueError("Unexpectedly large archive member")
            source = temp / "source.tif"
            with z.open(matches[0]) as incoming, source.open("wb") as outgoing:
                shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
        cropped = temp / "crop.tif"
        info = crop(source, cropped, bbox)
        info.update(year=year, status="downloaded", url=url, catalogue=CATALOGUE,
                    local_archive=bool(local_archive), archive_sha256=source_hash, archive_bytes=size,
                    retrieved_utc=datetime.now(timezone.utc).isoformat(), crop_sha256=digest(cropped))
        cropped.rename(path)
        meta.write_text(json.dumps(info, indent=2) + "\n")
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1988)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--max-archive-gib", type=float, default=2.5)
    parser.add_argument("--output", type=Path, default=Path("data/raw/woodland"))
    parser.add_argument("--download", action="store_true", help="Without this, write a plan without downloading national archives")
    parser.add_argument("--local-archive", type=Path, help="Reuse one local ZIP; requires a single matching year")
    args = parser.parse_args()
    if args.local_archive and args.start_year != args.end_year:
        parser.error("Local archive requires a single year")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = plan(args.start_year, args.end_year)
    if args.download:
        for i, row in enumerate(rows):
            if row["url"]:
                rows[i] = download_year(row["year"], args.output, args.bbox, args.max_archive_gib, args.local_archive)
                print(f"Saved native regional woodland {row['year']}", flush=True)
    (args.output / "manifest.json").write_text(json.dumps({"bbox_wgs84": args.bbox, "years": rows}, indent=2) + "\n")
    print(f"Plan/coverage saved to {args.output / 'manifest.json'}; {sum(r['status']=='outside_product_years' for r in rows)} unsupported years.")
