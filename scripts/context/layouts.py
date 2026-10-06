"""Verify each downloaded height overview against its own bounded native header."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import rasterio

from scanfi import inspect

def verify(resource, cache):
    url = resource['url'].removesuffix('.ovr')
    name = url.rsplit('/', 1)[-1]
    native = inspect(url, cache / 'scanfi' / name)
    if native['status'] != 'inspected':
        print(f"Header not inspected: {name}: {native.get('error')}", flush=True)
        return {'native': native, 'status': 'not_verified', 'overview_sha256': resource['sha256']}
    with rasterio.open(cache / 'scanfi-overviews' / (name + '.ovr')) as image:
        assert image.width == 11150 and image.height == 7444
        assert image.nodata == 255 and image.dtypes == ('uint8',)
        assert image.tags(1)['RESAMPLING'] == 'NEAREST'
        overview = {'width': image.width, 'height': image.height, 'nodata': image.nodata,
                    'dtype': image.dtypes[0], 'resampling': image.tags(1)['RESAMPLING'],
                    'scales': image.scales, 'offsets': image.offsets,
                    'crs_present': image.crs is not None}
    assert native['width'] == 178400 and native['height'] == 119100
    assert native['model_pixel_scale'] == (30.0, 30.0, 0.0)
    assert native['model_tiepoint'] == (0.0, 0.0, 0.0, -2341500.0, 9436500.0, 0.0)
    print(f'Verified native/overview grid: {name}', flush=True)
    return {'status': 'verified', 'native': native, 'overview': overview, 'overview_sha256': resource['sha256'],
            'overview_factor': 16, 'effective_resolution_m': 480,
            'georeference': 'Explicit native tiepoint / 30m pixel scale ×16; CRS from source README and GeoTIFF parameters.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    parser.add_argument('--acquisition', type=Path, default=Path('docs/data/scanfi_overviews.json'))
    parser.add_argument('--output', type=Path, default=Path('docs/data/scanfi_layouts.json'))
    args = parser.parse_args()
    acquisition = json.loads(args.acquisition.read_text())
    with ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(lambda resource: verify(resource, args.cache), acquisition['records']))
    output = {'purpose': 'Numerical context eligibility and grid verification, not model fitting',
              'records': records,
              'readme_crs': '+proj=lcc +lat_0=0 +lon_0=-95 +lat_1=49 +lat_2=77 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs',
              'units': 'Forest height metres per official README; nearest overview retains byte values.',
              'limitations': ['480m sparse nearest samples are not native-area-weighted 30m provincial means.',
                              'Retrospective LandTrendr reconstruction uses the full observation series.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n')
