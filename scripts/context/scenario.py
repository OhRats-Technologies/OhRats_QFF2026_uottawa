"""Build historical-position game seeds from the audited Ontario display geometry."""
import hashlib
import json
from pathlib import Path

import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom

ROOT = Path(__file__).resolve().parents[2]


def main():
    map_path = ROOT / 'web/presentation/assets/map.json'
    boundary = ROOT / 'data/raw/boundaries/ontario-2021.geojson'
    raster = ROOT / 'data/raw/woodland/woodland-2021.tif'
    source = json.loads(map_path.read_text())
    width, height = source['width'], source['height']
    pool = []
    occupied = set()
    with rasterio.open(raster) as src:
        affine = src.transform * src.transform.scale(src.width / width, src.height / height)
        geoms = [transform_geom('EPSG:4326', src.crs, f['geometry'])
                 for f in json.loads(boundary.read_text())['features']]
        inside = geometry_mask(geoms, out_shape=(height, width), transform=affine, invert=True)
        for point in source['points']:
            x, y = point['x'], point['y']
            col, row = int(x), int(y)
            if not (0 <= col < width and 0 <= row < height and inside[row, col]):
                continue
            code = int(next(src.sample([affine * (x, y)]))[0])
            if code not in {210, 220, 230}:
                continue
            # Spatial thinning is for selectable game markers, not statistical sampling.
            cell = (int(x / width * 18), int(y / height * 18))
            if cell in occupied:
                continue
            occupied.add(cell)
            pool.append({'x': round(x / width, 6), 'y': round(y / height, 6), 'cover': code})
    assert len(pool) >= 14
    result = {'role': 'historical positions seed fictional game incidents', 'year': 2021,
              'pool': pool, 'count': len(pool),
              'city_controls': source['cities'], 'width': width, 'height': height,
              'sources_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [map_path, boundary, raster]},
              'source_parent_hashes': source['source_sha256'],
              'method': 'Only inside-province recorded display positions with source forest classes 210/220/230; spatially thinned to one marker per 18x18 display cell. Original recorded area does not enter game pressure.',
              'limitation': 'Raw historical positions have coordinate/identity uncertainty. Game timing, fuel, exposure, weather, growth and interventions are fictional; these are not actual 2021 trajectories or operational forecasts.'}
    out = ROOT / 'web/demo/assets/context/scenario.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print('Saved', len(pool), 'spatially separated forest-position seeds; no labels/model changes.')


if __name__ == '__main__':
    main()
