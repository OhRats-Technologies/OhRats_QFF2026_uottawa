"""Render verified coarse height samples on the game's full Ontario display grid."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from rasterio.features import geometry_mask
from rasterio.transform import Affine, from_bounds
from rasterio.warp import reproject, transform_geom
from rasterio.enums import Resampling

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / '.cache/context/scanfi-height-v1')
    parser.add_argument('--output', type=Path, default=ROOT / 'web/demo/assets/context')
    parser.add_argument('--grid', type=Path, default=ROOT / 'web/demo/assets/context/layers.json')
    parser.add_argument('--boundary', type=Path, default=ROOT / 'data/raw/boundaries/ontario-2021.geojson')
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    layers = json.loads(args.grid.read_text())
    shape = (layers['height'], layers['width'])
    affine = from_bounds(*layers['bounds'], layers['width'], layers['height'])
    boundary = json.loads(args.boundary.read_text())
    geoms = [transform_geom('EPSG:4326', layers['crs'], row['geometry']) for row in boundary['features']]
    inside = geometry_mask(geoms, out_shape=shape, transform=affine, invert=True)
    stops = np.array([[19, 44, 51], [45, 86, 76], [107, 163, 116], [215, 228, 170]])
    legend = Image.new('RGB', (264, 61), '#eff2e9')
    draw = ImageDraw.Draw(legend)
    for x in range(240):
        colour = [int(np.interp(x / 239, [0, .25, .65, 1], stops[:, c])) for c in range(3)]
        draw.line([(12 + x, 12), (12 + x, 28)], fill=tuple(colour))
    draw.text((12, 36), '0 m                 15              30+', fill='#203a36')
    legend.save(output / 'height-legend.png')
    records = []
    for year in range(1985, 2020, 5):
        source = args.input / f'{year}.npz'
        with np.load(source) as saved:
            height = saved['height'].copy()
            height[~saved['inside']] = 255
            target = np.full(shape, 255, dtype='uint8')
            reproject(height, target, src_transform=Affine(*saved['transform'][:6]),
                      src_crs=str(saved['crs']), src_nodata=255, dst_transform=affine,
                      dst_crs=layers['crs'], dst_nodata=255, resampling=Resampling.nearest)
        values = np.clip(target / 30, 0, 1)
        rgba = np.zeros((*shape, 4), dtype='uint8')
        for channel in range(3):
            rgba[:, :, channel] = np.interp(values, [0, .25, .65, 1], stops[:, channel])
        rgba[inside & (target == 255), :3] = [64, 84, 91]
        rgba[inside, 3] = 255
        image = Image.fromarray(rgba)
        pen = ImageDraw.Draw(image)
        for geom in geoms:
            polygons = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
            for polygon in polygons:
                for ring in polygon:
                    pen.line([(~affine) * (x, y) for x, y in ring], fill='#b4c7bb', width=2)
        path = output / f'height-{year}.png'
        image.save(path)
        records.append({'year': year, 'image': f'assets/context/{path.name}',
                        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {'dataset_id': '07653869-f303-46c2-a04e-9ab479b73cbf',
                'role': 'dated visual context; does not change gameplay or the submitted predictor',
                'units': 'height metres; fixed colour scale 0-30+, nodata grey',
                'native_resolution_m': 30, 'sample_resolution_m': 480,
                'display_crs': layers['crs'], 'resampling': 'nearest',
                'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'colour_scale_m': [0, 7.5, 19.5, 30], 'colours_rgb': stops.tolist(),
                'limitations': 'Full-series retrospective reconstruction; not observed as-of forecasts or tree density.',
                'records': records}
    (output / 'height-series.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'epochs': len(records), 'shape': shape, 'role': manifest['role']}))


if __name__ == '__main__':
    main()
