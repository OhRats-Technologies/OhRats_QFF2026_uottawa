"""Index prepared numeric and display assets without downloading or fitting."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def build_manifest(prepared):
    context = read(prepared / 'height-context.json')
    series = read(prepared / 'maps/height-series.json')
    renderer = ROOT / 'scripts/context/render_height.py'
    producer_hash = hashlib.sha256(renderer.read_bytes()).hexdigest()
    if series.get('renderer_sha256') != producer_hash:
        raise ValueError('Height renderer provenance does not match the current renderer; reproduce the maps')
    layers_path = prepared / 'maps/layers.json'
    grid_path = layers_path if layers_path.exists() else ROOT / 'web/demo/assets/context/layers.json'
    grid = read(grid_path)
    assets = []

    def add(path, role, expected=None, **metadata):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError(f'Prepared asset differs from its receipt: {path.name}')
        assets.append({'path': path.relative_to(prepared).as_posix(), 'role': role,
                       'bytes': path.stat().st_size, 'sha256': digest, **metadata})

    for record in series['records']:
        year = record['year']
        add(prepared / 'arrays' / f'{year}.npz', 'numeric_height_samples',
            record['source_sha256'], year=year, units='m')
        add(prepared / 'maps' / Path(record['image']).name, 'styled_height_image',
            record['image_sha256'], year=year, numeric_predictor=False)
    add(prepared / 'maps/height-legend.png', 'display_legend', numeric_predictor=False)
    if layers_path.exists():
        for layer in grid['layers']:
            add(prepared / 'maps' / Path(layer['image']).name, 'styled_wms_image',
                layer['output_sha256'], layer=layer['key'], year=layer['year'],
                dataset_id=layer['dataset_id'], numeric_predictor=False)
            add(prepared / 'maps' / Path(layer['legend']).name, 'display_legend',
                layer=layer['key'], numeric_predictor=False)
    receipts = ['overviews.json', 'layouts.json', 'height-context.json', 'maps/height-series.json']
    if layers_path.exists():
        receipts.append('maps/layers.json')
    derived = {}
    change_path = prepared / 'change/summary.json'
    if change_path.exists():
        change = read(change_path)
        actual = hashlib.sha256((ROOT / 'scripts/context/change.py').read_bytes()).hexdigest()
        if change['code_sha256'] != actual:
            raise ValueError('Derived context producer changed; reproduce the comparison')
        actual = hashlib.sha256((ROOT / 'experiments/height_spatial_change.json').read_bytes()).hexdigest()
        if change['plan_sha256'] != actual:
            raise ValueError('Derived context plan changed')
        actual = hashlib.sha256((ROOT / 'scripts/context/render_change.py').read_bytes()).hexdigest()
        if change['map']['renderer_sha256'] != actual:
            raise ValueError('Derived context renderer changed; reproduce the comparison')
        if change['source_array_hashes'] != {str(r['year']): r['source_sha256'] for r in series['records']}:
            raise ValueError('Derived context uses different numeric sources')
        add(prepared / 'change/height-change.npz', 'numeric_height_difference', change['numeric_sha256'],
            units='m', dtype='int16', nodata=-32768, valid_zero=True, endpoints=change['endpoints'])
        add(prepared / 'change/histogram.csv', 'height_difference_histogram', change['histogram_sha256'])
        for key, role in [('image', 'styled_height_difference'), ('legend', 'display_legend')]:
            add(prepared / 'change' / Path(change['map'][key]).name, role,
                change['map'][f'{key}_sha256'], numeric_predictor=False)
        receipts.append('change/summary.json')
        derived = {'height_difference': {'epochs': change['endpoints'], 'mask': 'common valid across seven epochs',
                   'npz_keys': {'difference': 'signed metres; numerical extremes retained',
                                'common': 'boolean common footprint', 'transform': 'native affine', 'crs': 'native WKT'},
                   'colour_limits_m': [-10, 10], 'interpretation': 'Retrospective estimates, not observed growth or disturbance'}}
    return {
        'schema_version': 1,
        'role': 'Retrospective forest context; no fitted predictor or as-of availability claim',
        'paths_relative_to': 'directory containing this manifest',
        'numeric_grid': {
            'shape': context['shape'], 'affine_row_major_3x3': context['transform'],
            'crs_wkt': context['crs'], 'sample_resolution_m': context['effective_resolution_m'],
            'height_dtype': 'uint8', 'nodata': 255, 'valid_zero': True,
            'npz_keys': {'height': 'metres', 'inside': 'boolean Ontario mask',
                         'transform': 'row-major 3x3 affine', 'crs': 'scalar WKT string'},
            'resampling': 'source NEAREST overview; not native-pixel area averaging',
        },
        'display_grid': {'crs': grid['crs'], 'bounds': grid['bounds'],
                         'shape': [grid['height'], grid['width']],
                         'boundary_sha256': grid['boundary_sha256'],
                         'recipe_sha256': hashlib.sha256(grid_path.read_bytes()).hexdigest()},
        'assets': assets,
        'rendering': {'producer': 'scripts/context/render_height.py',
                      'sha256': producer_hash, 'identity_checked': True},
        'derived_context': derived,
        'receipts': [{'path': name, 'sha256': hashlib.sha256((prepared / name).read_bytes()).hexdigest()}
                     for name in receipts],
        'validation': 'Asset hashes checked against renderer receipts and current producer source; '
                      'grid semantics come from the extraction receipt, not a new raster audit.',
        'limitations': context['limitations'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    args = parser.parse_args()
    prepared = args.prepared.resolve()
    if not prepared.is_relative_to(ROOT / '.cache'):
        parser.error('Prepared directory must be under this repository’s ignored .cache/')
    result = build_manifest(prepared)
    (prepared / 'asset-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'assets': len(result['assets']), 'schema_version': 1,
                      'predictor_fits': 0, 'hardware_jobs': 0}))


if __name__ == '__main__':
    main()
