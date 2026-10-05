"""Coarse equal-area provincial land-cover summaries, never rectangle totals."""

from pathlib import Path
import hashlib
import json
import math
import time

import numpy as np
import rasterio
from rasterio.features import geometry_mask, bounds
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_geom, Resampling


def file_hash(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def province_geometry(path):
    features = json.loads(Path(path).read_text())['features']
    if len(features) != 1 or features[0]['properties']['PRUID'] != '35':
        raise ValueError('Boundary must contain only Ontario province 35')
    return transform_geom('EPSG:4326', 'EPSG:6933', features[0]['geometry'])


def grid(geometry, resolution):
    left, bottom, right, top = bounds(geometry)
    left, bottom = math.floor(left / resolution) * resolution, math.floor(bottom / resolution) * resolution
    right, top = math.ceil(right / resolution) * resolution, math.ceil(top / resolution) * resolution
    width, height = round((right - left) / resolution), round((top - bottom) / resolution)
    transform = from_origin(left, top, resolution, resolution)
    mask = geometry_mask([geometry], (height, width), transform, invert=True)
    return transform, mask


def summarize(path, geometry, resolution, treed_codes, save_grid=None):
    """Nearest-neighbor samples at equal-area cell centers, not exhaustive 30m area."""
    start = time.perf_counter()
    transform, mask = grid(geometry, resolution)
    with rasterio.Env(GDAL_CACHEMAX=128 * 1024 * 1024):
        with rasterio.open(path) as source:
            with WarpedVRT(source, crs='EPSG:6933', transform=transform,
                           height=mask.shape[0], width=mask.shape[1], nodata=255,
                           resampling=Resampling.nearest, warp_mem_limit=64) as coarse:
                values = coarse.read(1)
    province_values = values[mask]
    counts = np.bincount(province_values, minlength=256)
    total = int(mask.sum())
    known = total - int(counts[0] + counts[255])
    if not known:
        raise ValueError('No classified province cells')
    if save_grid is not None:
        saved = values.copy()
        saved[~mask] = 255
        with rasterio.open(save_grid, 'w', driver='GTiff', width=mask.shape[1],
                           height=mask.shape[0], count=1, dtype='uint8', crs='EPSG:6933',
                           transform=transform, nodata=255, compress='DEFLATE') as target:
            target.write(saved, 1)
    return dict(resolution_m=resolution, province_cells=total, classified_cells=known,
                approximate_province_area_km2=total * resolution ** 2 / 1e6,
                treed_fraction=float(sum(counts[code] for code in treed_codes) / known),
                water_fraction=float(counts[20] / known),
                unclassified_fraction=float(counts[0] / total),
                uncovered_fraction=float(counts[255] / total),
                class_counts={str(i): int(v) for i, v in enumerate(counts) if v},
                wall_seconds=time.perf_counter() - start)


def resolution_gate(coarse, fine, plan):
    difference = max(abs(coarse[name] - fine[name]) for name in ['treed_fraction', 'water_fraction'])
    coverage = max(coarse['uncovered_fraction'], fine['uncovered_fraction'])
    accepted = (difference <= plan['max_probe_fraction_difference']
                and coverage <= plan['max_uncovered_fraction'])
    return dict(accepted=bool(accepted), maximum_fraction_difference=difference,
                maximum_uncovered_fraction=coverage)
