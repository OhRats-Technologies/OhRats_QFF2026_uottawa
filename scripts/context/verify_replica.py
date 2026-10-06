"""Compare prepared context with published source, grid and image evidence; no fits."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(replica, cache):
    downloads = read(replica / 'overviews.json')
    original = read(ROOT / 'docs/data/scanfi_overviews.json')
    source_pairs = {row['url']: row['sha256'] for row in original['records']}
    source_matches = {row['url'] for row in downloads['records']} == set(source_pairs)
    source_matches &= len(downloads['records']) == 7
    for row in downloads['records']:
        actual = digest(cache / 'scanfi-overviews' / row['url'].rsplit('/', 1)[-1])
        source_matches &= actual == row['sha256'] == source_pairs.get(row['url'])
    layouts = read(replica / 'layouts.json')
    published = read(ROOT / 'docs/data/scanfi_layouts.json')
    fields = ['url', 'width', 'height', 'mode', 'compression', 'tile_width', 'tile_height',
              'model_pixel_scale', 'model_tiepoint', 'geo_keys', 'nodata', 'geo_double_params']
    grids_match = len(layouts['records']) == len(published['records']) == 7
    for current, previous in zip(layouts['records'], published['records']):
        grids_match &= current['status'] == 'verified'
        grids_match &= current['overview'] == previous['overview']
        grids_match &= all(current['native'][key] == previous['native'][key] for key in fields)
    context = read(replica / 'height-context.json')
    series = read(replica / 'maps/height-series.json')
    active_series = read(ROOT / 'web/demo/assets/context/height-series-v2.json')
    producer_match = series.get('renderer_sha256') == digest(ROOT / 'scripts/context/render_height.py')
    producer_match &= series['renderer_sha256'] == active_series['renderer_sha256']
    producer_match &= all(series[key] == active_series[key] for key in
                          ['records', 'dataset_id', 'display_crs', 'resampling',
                           'native_resolution_m', 'sample_resolution_m', 'colour_scale_m', 'colours_rgb'])
    previous = read(ROOT / 'docs/data/scanfi_height_context.json')
    fields = ['shape', 'transform', 'crs', 'years', 'rows', 'controls', 'common_mean_range_m']
    numeric_match = all(context[key] == previous[key] for key in fields)
    arrays_match = True
    for year in range(1985, 2020, 5):
        with np.load(replica / 'arrays' / f'{year}.npz') as current, np.load(
                ROOT / '.cache/context/scanfi-height-v1' / f'{year}.npz') as original_arrays:
            arrays_match &= set(current.files) == set(original_arrays.files)
            arrays_match &= all(np.array_equal(current[key], original_arrays[key])
                                for key in original_arrays.files)
    maps = []
    for image in sorted((replica / 'maps').glob('*.png')):
        published_image = ROOT / 'web/demo/assets/context' / image.name
        maps.append({'file': image.name, 'replica_sha256': digest(image),
                     'published_sha256': digest(published_image),
                     'identical': digest(image) == digest(published_image)})
    expected = {f'height-{year}.png' for year in range(1985, 2020, 5)} | {'height-legend.png'}
    expected |= {f'{key}{suffix}.png' for key in ['canopy', 'lorey', 'recovery', 'water', 'fuel']
                 for suffix in ['', '-legend']}
    images_complete = {row['file'] for row in maps} == expected
    grid = read(replica / 'maps/layers.json')
    published_grid = read(ROOT / 'web/demo/assets/context/layers.json')
    display_match = all(grid[key] == published_grid[key]
                        for key in ['bounds', 'crs', 'width', 'height', 'boundary_sha256'])
    display_match &= digest(cache / 'ontario-2021.geojson') == grid['boundary_sha256']
    receipt = read(replica / 'pipeline-receipt.json')
    prepared = receipt['status'] == 'prepared' and receipt['stages_completed'] == 7 + int(receipt.get('include_change', False))
    derived_present = (replica / 'change/summary.json').exists()
    if derived_present:
        from manifest import build_manifest
        manifest = build_manifest(replica)
        prepared &= 'height_difference' in manifest['derived_context']
    prepared &= not receipt.get('include_change') or derived_present
    equivalent = prepared and source_matches and grids_match and numeric_match and arrays_match
    equivalent &= producer_match and display_match and images_complete and all(row['identical'] for row in maps)
    return {'checked_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'identical_context' if equivalent else 'context_difference',
            'pipeline_receipt': receipt, 'seven_overview_sources_identical': source_matches,
            'scope': 'Base context equivalence; optional derived differences have separate hash checks, not new source accuracy validation',
            'optional_derived_context_hashes_checked': derived_present,
            'seven_native_overview_grids_identical': grids_match,
            'extracted_statistics_and_city_controls_identical': numeric_match,
            'seven_extracted_arrays_identical': arrays_match,
            'renderer_provenance_and_epoch_metadata_match': producer_match,
            'display_grid_and_boundary_identical': display_match,
            'expected_eighteen_images_present': images_complete, 'images': maps,
            'code_hashes': {name: digest(ROOT / 'scripts/context' / name)
                            for name in ['pipeline.py', 'bootstrap.py', 'overview.py', 'scanfi.py',
                                         'layouts.py', 'extract.py', 'render_height.py', 'wms.py',
                                         'verify_replica.py']},
            'predictor_fits': 0, 'quantum_states': 0, 'hardware_jobs': 0,
            'limitation': 'Context acquisition/rendering equivalence, not predictor replication. '
                          'Fresh WMS styles or metadata may drift in later acquisitions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replica', type=Path, default=ROOT / '.cache/context/prepared-replica')
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/context/source-replica')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compare(args.replica, args.cache)
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(json.dumps({key: value for key, value in result.items() if key != 'images'}, indent=2))
    if result['status'] != 'identical_context':
        raise SystemExit('Context differs: retained receipt identifies source or rendering drift')


if __name__ == '__main__':
    main()
