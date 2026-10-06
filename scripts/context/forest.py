"""Bounded forest-source acquisition and Ontario aggregation; no model execution."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.context.coarse_range import layout,acquire,write
from scripts.context.forest_extract import summarize


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root, output, header_cache):
    start=time.perf_counter()
    plan_path=root/'experiments/forest_expansion_acquisition.json'
    plan=json.loads(plan_path.read_text())
    for name,expected in plan['source_hashes'].items():
        if digest(root/name)!=expected:
            raise ValueError(f'Pinned source changed: {name}')
    files=['scripts/context/forest.py','scripts/context/coarse_range.py',
           'scripts/context/tiff_metadata.py','scripts/context/forest_extract.py']
    pins={name:digest(root/name) for name in files}
    intent=dict(plan_sha256=digest(plan_path),code_sha256=pins)
    output.mkdir(parents=True,exist_ok=True)
    if (output/'intent.json').exists():
        if json.loads((output/'intent.json').read_text())!=intent:
            raise ValueError('Acquisition intent changed; preserve the original namespace')
    else:
        write(output/'intent.json',intent)
    directory=(root/'.cache/catalogue/20261006/guides/scanfi-directory.raw').read_text()
    advertised=set(re.findall(r'href="([^"]+)"',directory))
    tasks=[]
    for key,spec in plan['layers'].items():
        for epoch in plan['epochs']:
            pattern=fr"{spec['prefix']}_{epoch}_v2_\d+\.tif"
            names=[name for name in advertised if re.fullmatch(pattern,name)]
            if len(names)!=1 or names[0]+'.ovr' not in advertised:
                raise ValueError(f'No unique advertised numerical source: {key}, {epoch}')
            tasks.append((key,epoch,names[0],spec['factor']))

    def inspect(task):
        key,epoch,name,factor=task
        record=layout(name,factor,plan,header_cache)
        record.update(layer=key,epoch=epoch)
        target=output/'resources'/name
        target.mkdir(parents=True,exist_ok=True)
        write(target/'layout.json',record)
        print(f'Layout verified: {key}, {epoch}, {30*factor}m',flush=True)
        return record

    with ThreadPoolExecutor(max_workers=plan['budget']['parallel_downloads']) as executor:
        records=list(executor.map(inspect,tasks))
    metadata_bytes=sum(r['metadata_bytes'] for record in records for r in record['source_records'])
    pixel_bytes=sum(r['stop']-r['start'] for r in records)
    if metadata_bytes+pixel_bytes>plan['budget']['total_source_bytes']:
        raise ValueError('Planned source reads exceed total budget; no pixels requested')
    write(output/'layouts.json',dict(records=records,metadata_bytes=metadata_bytes,pixel_bytes=pixel_bytes))
    with ThreadPoolExecutor(max_workers=plan['budget']['parallel_downloads']) as executor:
        proofs=list(executor.map(lambda r:acquire(r,output/'resources'/r['name']),records))
    summaries=[summarize(r,plan,header_cache,output/'resources'/r['name'],root) for r in records]
    assets={str((output/'resources'/r['name']/'ontario.npz').relative_to(root)):
            digest(output/'resources'/r['name']/'ontario.npz') for r in records}
    source=dict(status='acquired',plan_sha256=digest(plan_path),code_sha256=pins,
        source_hashes=plan['source_hashes'],records=records,pixel_proofs=proofs,
        metadata_bytes=metadata_bytes,pixel_bytes=sum(p['bytes'] for p in proofs),
        seconds=time.perf_counter()-start,derived_arrays_sha256=assets)
    result=dict(status='summarized',rows=summaries,crs=plan['crs'],
        source='docs/data/forest_feature_sources.json',plan_sha256=digest(plan_path),
        aggregation=plan['aggregation'],time_policy=plan['time_policy'],
        recovery_policy=plan['recovery_policy'],final_test_accessed=False)
    write(output/'source.json',source)
    write(output/'summary.json',result)
    write(root/'docs/data/forest_feature_sources.json',source)
    write(root/'docs/data/forest_feature_summary.json',result)
    return dict(layers=len(plan['layers']),epochs=len(plan['epochs']),source_bytes=metadata_bytes+pixel_bytes,
                seconds=source['seconds'],fits=0,hardware_jobs=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/context/forest-features-v2')
    parser.add_argument('--header-cache',type=Path,default=ROOT/'.cache/context/forest-selective-layout-v1')
    args=parser.parse_args()
    print(json.dumps(run(ROOT,args.output.resolve(),args.header_cache.resolve()),indent=2))
