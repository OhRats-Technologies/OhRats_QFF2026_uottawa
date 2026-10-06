"""Verify completed forest caches, masks and source ranges without downloads."""
import json
import re
import sys
from pathlib import Path
import numpy as np
from rasterio.warp import transform
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from wildfire_lab.forest_run import digest, write
from scripts.context.forest_extract import region


def audit(root):
    source = json.loads((root/'docs/data/forest_feature_sources.json').read_text())
    summary = json.loads((root/'docs/data/forest_feature_summary.json').read_text())
    plan_path = root/'experiments/forest_expansion_acquisition.json'
    plan = json.loads(plan_path.read_text())
    assert digest(plan_path)==source['plan_sha256']==summary['plan_sha256']
    for name, expected in plan['source_hashes'].items():
        assert digest(root/name)==expected
    for name, expected in source['derived_arrays_sha256'].items():
        assert digest(root/name)==expected
    stats = {(r['epoch'],r['layer']):r for r in summary['rows']}
    assert len(stats)==len(plan['epochs'])*len(plan['layers'])==42
    proof = {r['url']:r for r in source['pixel_proofs']}
    windows = {factor:region(plan,factor,root) for factor in [16,32]}
    pixel_bytes, metadata_bytes, checked = 0, 0, []
    for record in source['records']:
        name, factor = record['name'], record['factor']
        resource = root/'.cache/context/forest-features-v2/resources'/name
        header_root = root/'.cache/context/forest-selective-layout-v1'
        for metadata in record['source_records']:
            metadata_name = metadata['url'].rsplit('/',1)[1]
            for request in metadata['requests']:
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',request['content_range'])
                assert match and request['url']==metadata['url']
                start,end,total = map(int,match.groups())
                target = header_root/metadata_name/f'{start}.bin'
                assert target.stat().st_size==end-start+1 and total==metadata['size_bytes']
                assert digest(target)==request['sha256']
                metadata_bytes += target.stat().st_size
        native = record['source_records'][0]['frames'][0]['tags']
        grid = plan['native_grid']
        for tag,field in [('256','width'),('257','height'),('33550','pixel_scale'),
                          ('33922','tiepoint'),('34736','geo_double_params')]:
            assert native[tag]==grid[field]
        frame = record['frame']['tags']
        assert (frame['256'],frame['257'])==((grid['width']+factor-1)//factor,
                                            (grid['height']+factor-1)//factor)
        assert float(frame['42113'])==float(native['42113'])==record['nodata']
        eligible = 'NEAREST' in frame.get('42112','')
        assert record['model_eligible']==eligible
        assert eligible or name in plan['allowed_unadvertised_resampling']
        receipt = proof[record['source_records'][1]['url']]
        assert digest(resource/'frame.bin')==receipt['sha256']
        assert (resource/'frame.bin').stat().st_size==receipt['bytes']==record['stop']-record['start']
        assert receipt['content_range']==f"bytes {record['start']}-{record['stop']-1}/{record['source_records'][1]['size_bytes']}"
        pixel_bytes += receipt['bytes']
        window, affine, inside = windows[factor]
        with np.load(resource/'ontario.npz') as archive:
            values,valid = archive['values'],archive['valid']
            np.testing.assert_array_equal(archive['inside'],inside)
            np.testing.assert_allclose(archive['transform'],np.array(affine),atol=1e-10)
            np.testing.assert_array_equal(valid,inside & np.isfinite(values) & (values!=record['nodata']))
            s = stats[(record['epoch'],record['layer'])]
            selected = values[valid]
            assert s['inside_samples']==int(inside.sum()) and s['valid_samples']==len(selected)
            assert s['model_eligible']==eligible and s['nodata']==record['nodata']
            np.testing.assert_allclose([selected.mean(),selected.min(),selected.max(),(selected==0).mean()],
                                       [s['mean'],s['minimum'],s['maximum'],s['zero_fraction']],atol=1e-10)
            np.testing.assert_allclose(np.percentile(selected,[10,50,90]),s['p10_p50_p90'],atol=1e-10)
            assert values.dtype.kind==('i' if frame['339']==2 else 'u')
        checked.append(dict(layer=record['layer'],epoch=record['epoch'],model_eligible=eligible,
                            valid_samples=s['valid_samples'],mean=s['mean']))
    assert pixel_bytes==source['pixel_bytes'] and metadata_bytes==source['metadata_bytes']
    assert pixel_bytes+metadata_bytes<=plan['budget']['total_source_bytes']
    cities = []
    for name,lon,lat in [('Toronto',-79.3832,43.6532),('Windsor',-83.0364,42.3149),
                         ('Ottawa',-75.6972,45.4215),('Thunder Bay',-89.2477,48.3809)]:
        x,y = transform('EPSG:4326',plan['crs'],[lon],[lat])
        _,affine,inside = windows[16]
        col,row = ~affine*(x[0],y[0])
        assert inside[int(row),int(col)]
        longitude,latitude = transform(plan['crs'],'EPSG:4326',x,y)
        error = max(abs(longitude[0]-lon),abs(latitude[0]-lat))
        assert error<1e-9
        cities.append(dict(city=name,inside_ontario=True,roundtrip_error_degrees=error))
    return dict(status='verified',source_layers_checked=len(checked),rows=checked,city_controls=cities,
                source_bytes=pixel_bytes+metadata_bytes,source_sha256=digest(root/'docs/data/forest_feature_sources.json'),
                summary_sha256=digest(root/'docs/data/forest_feature_summary.json'),
                new_downloads=0,new_predictor_fits=0,new_quantum_evaluations=0,
                limitation='Checks saved compressed/header bytes and decoded-array hashes/masks/statistics. Does not independently re-decode all source pixels, certify native30m inventories or establish historical availability of reconstructed imagery.')


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = audit(ROOT)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    write(args.output,result)
    print(json.dumps({k:result[k] for k in ['status','source_layers_checked','source_bytes','new_downloads']}))
