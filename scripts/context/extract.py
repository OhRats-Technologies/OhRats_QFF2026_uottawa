"""Extract coarse, nearest-sampled Ontario height context from verified SCANFI overviews."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from rasterio.warp import transform, transform_bounds, transform_geom
from rasterio.windows import Window, from_bounds, transform as window_transform

ROOT = Path(__file__).resolve().parents[2]
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/catalogue/20261006')
    parser.add_argument('--layouts', type=Path, default=ROOT / 'docs/data/scanfi_layouts.json')
    parser.add_argument('--boundary', type=Path, default=ROOT / 'data/raw/boundaries/ontario-2021.geojson')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/context/scanfi-height-v1')
    parser.add_argument('--receipt', type=Path, default=ROOT / 'docs/data/scanfi_height_context.json')
    args = parser.parse_args()
    layouts_path = args.layouts.resolve()
    layouts = json.loads(layouts_path.read_text())
    assert len(layouts['records']) == 7 and all(r['status'] == 'verified' for r in layouts['records'])
    expected = [0.0, -95.0, 49.0, 77.0, 0.0, 0.0, 298.257222101004, 6378137.0]
    assert all(r['native']['geo_double_params'] == expected for r in layouts['records'])
    crs = CRS.from_string(layouts['readme_crs'])
    affine = Affine(480, 0, -2341500, 0, -480, 9436500)
    boundary_path = args.boundary.resolve()
    boundary = json.loads(boundary_path.read_text())
    geoms = [transform_geom('EPSG:4326', crs, f['geometry']) for f in boundary['features']]
    bounds = transform_bounds('EPSG:4326', crs, -95.156011, 41.676957, -74.320382, 56.861715, densify_pts=41)
    raw = from_bounds(*bounds, transform=affine)
    window = Window(np.floor(raw.col_off), np.floor(raw.row_off), np.ceil(raw.width) + 2, np.ceil(raw.height) + 2)
    local = window_transform(window, affine)
    shape = (int(window.height), int(window.width))
    inside = geometry_mask(geoms, out_shape=shape, transform=local, invert=True)
    arrays, years, rows = [], [], []
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    for record in layouts['records']:
        name = record['native']['url'].rsplit('/', 1)[-1] + '.ovr'
        year = int(name.split('_')[3])
        with rasterio.open(args.cache / 'scanfi-overviews' / name) as src:
            array = src.read(1, window=window, boundless=True, fill_value=255)
        assert array.shape == shape
        arrays.append(array)
        years.append(year)
        np.savez_compressed(output / f'{year}.npz', height=array, inside=inside,
                            transform=np.array(local), crs=str(crs))
    common = inside & np.logical_and.reduce([array != 255 for array in arrays])
    assert common.any()
    for year, array in zip(years, arrays):
        valid = inside & (array != 255)
        values = array[common]
        rows.append({'year': year, 'inside_samples': int(inside.sum()), 'valid_samples': int(valid.sum()),
                     'valid_fraction': float(valid.sum() / inside.sum()),
                     'common_samples': int(common.sum()), 'common_mean_height_m': float(values.mean()),
                     'common_height_p10_p50_p90_m': np.percentile(values, [10, 50, 90]).tolist(),
                     'zero_height_samples': int((values == 0).sum())})
    map_source = json.loads((ROOT / 'web/presentation/assets/map.json').read_text())
    controls = []
    for city in map_source['cities']:
        x, y = transform('EPSG:4326', crs, [city['longitude']], [city['latitude']])
        col, row = ~local * (x[0], y[0])
        lon, lat = transform(crs, 'EPSG:4326', x, y)
        controls.append({'name': city['name'], 'inside_mask': bool(inside[int(row), int(col)]),
                         'roundtrip_error_degrees': max(abs(lon[0] - city['longitude']), abs(lat[0] - city['latitude'])),
                         'heights_m_by_year': {year: None if array[int(row), int(col)] == 255 else int(array[int(row), int(col)])
                                              for year, array in zip(years, arrays)}})
    result = {'role': 'coarse retrospective province context, not native-area means or contemporaneous forecasts',
              'effective_resolution_m': 480, 'resampling': 'Source overview NEAREST; no averaging of native pixels',
              'nodata': 255, 'height_units': 'metres per official README; valid zero retained',
              'shape': shape, 'transform': list(local), 'crs': str(crs), 'years': years, 'rows': rows,
              'controls': controls, 'common_mean_range_m': float(np.ptp([r['common_mean_height_m'] for r in rows])),
              'source_hashes': {str(path.resolve().relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in [layouts_path, boundary_path, args.cache / 'guides/scanfi-readme.raw']},
              'limitations': ['Province polygon includes water; valid zeros are not automatically tree absence.',
                              '480m nearest samples approximate structure, not a 30m area-weighted inventory.',
                              'Only seven epochs, five years apart; annual carry-forward repeats inputs.',
                              'LandTrendr/full-series reconstruction uses future observations relative to historical years.',
                              'No improvement or independent validation is established by nonzero temporal variation.']}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'rows': rows, 'controls': controls, 'range_m': result['common_mean_range_m']}, indent=2))


if __name__ == '__main__':
    main()
