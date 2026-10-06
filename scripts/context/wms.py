"""Acquire bounded, aligned Ontario WMS context images; never numeric predictors."""
import argparse
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_bounds, transform_geom

ROOT = Path(__file__).resolve().parents[2]
NTEMS = 'https://opendata.nfis.org/mapserver/cgi-bin/wms_change.cgi'
FBP = 'https://ca.nfis.org/mapserver/cgi-bin/fbp_eng.cgi'
LAYERS = [
    ('canopy', '7cbdfae1-f724-4679-8f0f-1c611f17186f', NTEMS, 'CA_forest_elev_mean_2015_NN', 2015, 'Canopy height', 'm; styled image only'),
    ('lorey', '836082d5-d55f-46c3-9b9c-aaf1a306c247', NTEMS, 'CA_forest_loreys_height_2015_NN', 2015, "Lorey’s height", 'm; styled image only'),
    ('recovery', 'a6b81e8b-d429-4629-9121-5a56786fcb83', NTEMS, 'CA_forest_fire_years2recovery', 2017, 'Spectral recovery', 'years to 80% spectral recovery; censored classes require legend'),
    ('water', '0bce352f-6f3f-4a30-9763-c80805fcf272', NTEMS, 'CA_Water_2022', 2022, 'Mapped water', 'categorical water mask; styled image only'),
    ('fuel', '851e6a27-a250-41e6-9cd0-d7ff96455dd6', FBP, 'fpb100m2026', 2026, 'FBP fuel types', 'categorical; unmatched fuels are not zero risk'),
]
NS = {'w': 'http://www.opengis.net/wms'}


def request(url, target, budget=8_000_000):
    if target.exists():
        body = target.read_bytes()
        receipt = json.loads(target.with_suffix(target.suffix + '.receipt.json').read_text())
        assert hashlib.sha256(body).hexdigest() == receipt['sha256'], target
        return body, receipt
    with urlopen(url, timeout=45) as response:
        body = response.read(budget + 1)
        status = response.status
        content_type = response.headers.get('Content-Type')
    if len(body) > budget:
        raise ValueError('Response exceeds bounded download budget')
    receipt = {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
               'status': status, 'content_type': content_type, 'bytes': len(body),
               'sha256': hashlib.sha256(body).hexdigest()}
    target.write_bytes(body)
    target.with_suffix(target.suffix + '.receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return body, receipt


def collect(spec, output, cache, geoms, bounds, affine, shape):
    key, identifier, endpoint, layer_name, year, title, units = spec
    capability_path = cache / ('fbp-wms.xml' if endpoint == FBP else 'ntems-wms.xml')
    url = endpoint + '?' + urlencode(dict(SERVICE='WMS', REQUEST='GetCapabilities', VERSION='1.3.0'))
    caps, caps_receipt = request(url, capability_path)
    root = ET.fromstring(caps)
    layer = next(n for n in root.findall('.//w:Layer', NS)
                 if n.findtext('w:Name', namespaces=NS) == layer_name)
    advertised_crs = [c.text for c in layer.findall('w:CRS', NS)]
    crs = 'EPSG:3978' if 'EPSG:3978' in advertised_crs else 'EPSG:3857'
    if crs not in advertised_crs:
        raise ValueError('No supported projected display CRS')
    source_bounds = bounds if crs == 'EPSG:3978' else transform_bounds('EPSG:3978', crs, *bounds, densify_pts=41)
    height, width = shape
    params = dict(SERVICE='WMS', VERSION='1.3.0', REQUEST='GetMap', LAYERS=layer_name,
                  STYLES='', CRS=crs, BBOX=','.join(map(str, source_bounds)),
                  WIDTH=width, HEIGHT=height, FORMAT='image/png', TRANSPARENT='TRUE')
    body, receipt = request(endpoint + '?' + urlencode(params), cache / f'{key}.png')
    image = np.array(Image.open(io.BytesIO(body)).convert('RGBA'))
    if image.shape != (height, width, 4):
        raise ValueError('WMS image dimensions differ from requested window')
    source_affine = rasterio.transform.from_bounds(*source_bounds, width, height)
    if crs != 'EPSG:3978':
        warped = np.zeros_like(image)
        for channel in range(4):
            reproject(image[:, :, channel], warped[:, :, channel], src_transform=source_affine,
                      src_crs=crs, dst_transform=affine, dst_crs='EPSG:3978',
                      resampling=rasterio.enums.Resampling.nearest)
        image = warped
    inside = geometry_mask(geoms, out_shape=shape, transform=affine, invert=True)
    image[~inside, 3] = 0
    result = Image.fromarray(image)
    drawing = ImageDraw.Draw(result)
    for geom in geoms:
        polygons = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for polygon in polygons:
            for ring in polygon:
                drawing.line([(~affine) * (x, y) for x, y in ring], fill='#b4c7bb', width=2)
    result.save(output / f'{key}.png')
    legend_node = layer.find('.//w:LegendURL/w:OnlineResource', NS)
    legend_url = (legend_node.attrib['{http://www.w3.org/1999/xlink}href'] if legend_node is not None
                  else endpoint + '?' + urlencode(dict(SERVICE='WMS', VERSION='1.3.0',
                  REQUEST='GetLegendGraphic', SLD_VERSION='1.1.0', LAYER=layer_name,
                  FORMAT='image/png', STYLE='default')))
    legend_receipt = None
    legend_path = None
    try:
        legend_body, legend_receipt = request(legend_url, cache / f'{key}-legend-v2.png')
        Image.open(io.BytesIO(legend_body)).save(output / f'{key}-legend.png')
        legend_path = f'assets/context/{key}-legend.png'
    except Exception as error:
        legend_receipt = {'url': legend_url, 'status': 'failed', 'error': str(error)}
    return {'key': key, 'dataset_id': identifier, 'title': title, 'year': year, 'units': units,
            'layer': layer_name, 'role': 'dated_visual_context', 'numeric_predictor': False,
            'native_resolution_m': 100 if key == 'fuel' else 30,
            'display_crs': 'EPSG:3978', 'display_bounds': list(bounds),
            'display_shape': [height, width], 'resampling': 'nearest styled RGBA',
            'source_display_crs': crs, 'source_display_bounds': list(source_bounds),
            'alpha_pixels_inside': int(np.count_nonzero(image[inside, 3])),
            'image': f'assets/context/{key}.png', 'legend': legend_path,
            'output_sha256': hashlib.sha256((output / f'{key}.png').read_bytes()).hexdigest(),
            'request': receipt, 'capabilities': caps_receipt, 'legend_request': legend_receipt,
            'catalogue': 'https://open.canada.ca/data/en/dataset/' + identifier}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/catalogue/20261006/wms')
    parser.add_argument('--output', type=Path, default=ROOT / 'web/demo/assets/context')
    parser.add_argument('--grid', type=Path, default=ROOT / 'web/demo/assets/context/layers.json',
                        help='Committed display-grid recipe; avoids requiring the national cover raster')
    parser.add_argument('--boundary', type=Path, default=ROOT / 'data/raw/boundaries/ontario-2021.geojson')
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    boundary = args.boundary
    geoms = [transform_geom('EPSG:4326', 'EPSG:3978', f['geometry'])
             for f in json.loads(boundary.read_text())['features']]
    grid = json.loads(args.grid.read_text())
    assert grid['crs'] == 'EPSG:3978'
    bounds = tuple(grid['bounds'])
    height, width = grid['height'], grid['width']
    affine = rasterio.transform.from_bounds(*bounds, width, height)
    # Shared capabilities are acquired once before parallel image requests.
    for name, endpoint in [('ntems', NTEMS), ('fbp', FBP)]:
        request(endpoint + '?' + urlencode(dict(SERVICE='WMS', REQUEST='GetCapabilities', VERSION='1.3.0')), args.cache / f'{name}-wms.xml')
    def worker(spec):
        try:
            return collect(spec, args.output, args.cache, geoms, bounds, affine, (height, width))
        except Exception as error:
            return {'key': spec[0], 'dataset_id': spec[1], 'status': 'failed', 'error': str(error)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        layers = list(pool.map(worker, LAYERS))
    manifest = {'role': 'display context only; no new model inputs',
                'bounds': list(bounds), 'crs': 'EPSG:3978', 'width': width, 'height': height,
                'boundary_sha256': hashlib.sha256(boundary.read_bytes()).hexdigest(),
                'layers': layers}
    (args.output / 'layers.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps([{k: r.get(k) for k in ['key', 'status', 'alpha_pixels_inside', 'error']} for r in layers], indent=2))


if __name__ == '__main__':
    main()
