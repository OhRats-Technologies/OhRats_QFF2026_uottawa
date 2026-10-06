"""Fixed-scale visual explanation of retrospective height differences."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import Affine, from_bounds
from rasterio.warp import reproject, transform_geom

ROOT = Path(__file__).resolve().parents[2]
STOPS = np.array([[203, 126, 77], [221, 228, 221], [53, 151, 156]])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(delta, common, endpoints, context, boundary_path, output, plan):
    grid = json.loads((ROOT / 'web/demo/assets/context/layers.json').read_text())
    assert digest(boundary_path) == grid['boundary_sha256']
    shape = (grid['height'], grid['width'])
    affine = from_bounds(*grid['bounds'], grid['width'], grid['height'])
    nodata = plan['map']['numeric_nodata']

    def project(values):
        source = values.astype(np.int16)
        source[~common] = nodata
        target = np.full(shape, nodata, dtype=np.int16)
        reproject(source, target, src_transform=Affine(*context['transform'][:6]),
                  src_crs=context['crs'], src_nodata=nodata, dst_transform=affine,
                  dst_crs=grid['crs'], dst_nodata=nodata, resampling=Resampling.nearest)
        return target

    target = project(delta)
    first, last = [project(endpoints[y]) for y in plan['endpoints']]
    valid = target != nodata
    assert np.array_equal(valid, (first != nodata) & (last != nodata))
    assert np.array_equal(target[valid], last[valid] - first[valid])
    boundary = json.loads(boundary_path.read_text())
    geoms = [transform_geom('EPSG:4326', grid['crs'], r['geometry']) for r in boundary['features']]
    inside = geometry_mask(geoms, out_shape=shape, transform=affine, invert=True)
    rgba = np.zeros((*shape, 4), dtype=np.uint8)
    for c in range(3):
        rgba[:, :, c] = np.interp(target, [-10, 0, 10], STOPS[:, c])
    rgba[inside & ~valid, :3] = [64, 84, 91]
    rgba[inside, 3] = 255
    image = Image.fromarray(rgba)
    pen = ImageDraw.Draw(image)
    for geom in geoms:
        polygons = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for polygon in polygons:
            for ring in polygon:
                pen.line([(~affine) * (x, y) for x, y in ring], fill='#b4c7bb', width=2)
    image.save(output / 'height-change.png')
    legend = Image.new('RGB', (264, 61), '#eff2e9')
    draw = ImageDraw.Draw(legend)
    for x in range(240):
        color = tuple(int(np.interp(x / 239, [0, .5, 1], STOPS[:, c])) for c in range(3))
        draw.line([(12 + x, 12), (12 + x, 28)], fill=color)
    draw.text((12, 36), '-10 m              0              +10 m', fill='#203a36')
    legend.save(output / 'height-change-legend.png')
    return {'image': 'assets/context/height-change.png', 'legend': 'assets/context/height-change-legend.png',
            'image_sha256': digest(output / 'height-change.png'),
            'legend_sha256': digest(output / 'height-change-legend.png'),
            'renderer_sha256': digest(Path(__file__)), 'display_crs': grid['crs'],
            'shape': list(shape), 'colour_limits_m': [-10, 10], 'colours_rgb': STOPS.tolist(),
            'boundary_sha256': grid['boundary_sha256'], 'resampling': 'nearest',
            'projected_endpoint_subtraction_matches': True,
            'numeric_values_unclipped': True, 'missing_rgb': [64, 84, 91]}


def figure(result, histogram, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'width_ratios': [1, 1.15]})
    fig.suptitle('A small provincial mean hides offsetting height differences',
                 x=.045, ha='left', fontsize=17, fontweight='bold')
    axes[0].imshow(Image.open(output / 'height-change.png'))
    axes[0].axis('off')
    axes[0].set_title('Estimated 2015 height − estimated 1985 height', fontsize=11)
    inset = axes[0].inset_axes([.1, -.045, .8, .085])
    inset.imshow(Image.open(output / 'height-change-legend.png'))
    inset.axis('off')
    x = np.arange(-254, 255)
    keep = (x >= -30) & (x <= 30)
    colors = ['#bd784c' if value < 0 else '#358f96' if value > 0 else '#81908a' for value in x[keep]]
    axes[1].bar(x[keep], histogram[keep] / result['common_samples'], color=colors, width=.9)
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set(xlabel='Signed height difference (m)', ylabel='Share of common valid samples',
                xlim=(-30.5, 30.5), ylim=(0, max(histogram) / result['common_samples'] * 1.25))
    axes[1].grid(axis='y', alpha=.15)
    axes[1].set_title(f"Net mean {result['mean_signed_m']:+.2f} m · mean absolute {result['mean_absolute_m']:.2f} m",
                      fontsize=12, fontweight='bold')
    tail = int(histogram[~keep].sum()) / result['common_samples']
    fig.text(.045, .035, f'480 m nearest samples · common seven-epoch Ontario footprint · histogram tails beyond ±30 m: {tail:.3%}.\n'
             'Retrospective estimates; differences do not identify physical growth, disturbance or fire effects.',
             fontsize=10, color='#47555a')
    fig.tight_layout(rect=(.02, .13, 1, .91))
    fig.savefig(output / 'height-change-summary.png', dpi=180, facecolor='white')
    plt.close(fig)
