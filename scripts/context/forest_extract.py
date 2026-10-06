"""Per-epoch Ontario summaries with independent masks and audited native geometry."""
import json
import numpy as np
from PIL import Image
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import from_bounds, Window, transform as window_transform
from scripts.context.coarse_range import standalone_frame, write


def region(plan, factor, root):
    boundary=json.loads((root/plan['boundary']).read_text())
    geoms=[transform_geom('EPSG:4326',plan['crs'],f['geometry']) for f in boundary['features']]
    pixel=30*factor
    affine=Affine(pixel,0,-2341500,0,-pixel,9436500)
    bounds=transform_bounds('EPSG:4326',plan['crs'],-95.156011,41.676957,-74.320382,56.861715,densify_pts=41)
    raw=from_bounds(*bounds,transform=affine)
    window=Window(np.floor(raw.col_off),np.floor(raw.row_off),np.ceil(raw.width)+2,np.ceil(raw.height)+2)
    local=window_transform(window,affine)
    shape=(int(window.height),int(window.width))
    inside=geometry_mask(geoms,out_shape=shape,transform=local,invert=True)
    return window,local,inside


def summarize(record, plan, cache, directory, root):
    window,local,inside=region(plan,record['factor'],root)
    box=(int(window.col_off),int(window.row_off),int(window.col_off+window.width),
         int(window.row_off+window.height))
    stream=standalone_frame(record,cache,directory)
    with Image.open(stream) as image:
        if image.size!=(record['width'],record['height']):
            raise ValueError('Virtual coarse TIFF dimensions differ')
        # Decode only the selected coarse page, not the native or finer overviews.
        array=np.array(image.crop(box))
    if array.shape!=inside.shape:
        raise ValueError('Ontario window shape changed')
    valid=inside & np.isfinite(array) & (array!=record['nodata'])
    if not valid.any():
        raise ValueError('No valid Ontario numerical samples')
    values=array[valid]
    limits=plan['layers'][record['layer']]['range']
    if values.min()<limits[0] or values.max()>limits[1]:
        raise ValueError('Source values exceed declared physical audit bounds')
    np.savez_compressed(directory/'ontario.npz',values=array,inside=inside,valid=valid,
                        transform=np.array(local))
    summary=dict(layer=record['layer'],epoch=record['epoch'],
        resampling=record['resampling'],model_eligible=record['model_eligible'],
        units=plan['layers'][record['layer']]['units'],resolution_m=30*record['factor'],
        inside_samples=int(inside.sum()),valid_samples=int(valid.sum()),
        valid_fraction=float(valid.sum()/inside.sum()),zero_fraction=float(np.mean(values==0)),
        mean=float(values.mean()),p10_p50_p90=np.percentile(values,[10,50,90]).tolist(),
        minimum=float(values.min()),maximum=float(values.max()),nodata=record['nodata'],
        transform=list(local),shape=list(array.shape))
    write(directory/'summary.json',summary)
    print(f"Summarized {record['layer']}, {record['epoch']}: {summary['mean']:.3f}",flush=True)
    return summary
