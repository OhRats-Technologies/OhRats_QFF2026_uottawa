"""Locate/download one bounded coarse TIFF frame, retaining HTTP range proofs."""
from datetime import datetime, timezone
import hashlib
import io
import json
import struct
from urllib.request import Request, urlopen
from scripts.context.scanfi import BASE, RangeReader
from scripts.context.tiff_metadata import Header


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def layout(name, factor, plan, cache):
    records=[]
    for resource in [name,name+'.ovr']:
        stream=RangeReader(BASE+resource,cache/resource,
                           budget=plan['budget']['metadata_bytes_per_resource'])
        header=Header(stream)
        frames=list(header.frames()) if resource.endswith('.ovr') else [next(header.frames())]
        records.append(dict(url=BASE+resource,frames=frames,size_bytes=stream.size,
            metadata_bytes=sum(map(len,stream.blocks.values())),requests=stream.receipts))
    native=records[0]['frames'][0]['tags']
    grid=plan['native_grid']
    for key,field in [('256','width'),('257','height'),('33550','pixel_scale'),
                      ('33922','tiepoint'),('34736','geo_double_params')]:
        if native[key] != grid[field]:
            raise ValueError(f'Native grid differs: {name}, {field}')
    width=(grid['width']+factor-1)//factor
    height=(grid['height']+factor-1)//factor
    frame=next(f for f in records[1]['frames'] if
               f['tags']['256']==width and f['tags']['257']==height)
    tags=frame['tags']
    resampling='NEAREST' if 'NEAREST' in tags.get('42112','') else 'unadvertised'
    if resampling!='NEAREST' and name not in plan['allowed_unadvertised_resampling']:
        raise ValueError('Overview resampling requires an explicit source decision')
    if float(tags['42113']) != float(native['42113']):
        raise ValueError('Overview nodata does not match native value')
    if any(marker in tags.get('42112','').lower() for marker in ['scale','offset']):
        raise ValueError('Review explicit band transformation before numerical use')
    entries,_=header.directory(frame['ifd_offset'])
    offsets,counts=header.value(entries[324]),header.value(entries[325])
    start,stop=min(offsets),max(a+b for a,b in zip(offsets,counts,strict=True))
    if stop-start > plan['budget']['pixel_range_bytes_per_resource']:
        raise ValueError('Coarse frame exceeds bounded pixel budget')
    return dict(name=name,factor=factor,source_records=records,frame=frame,
                start=start,stop=stop,compressed_bytes=sum(counts),
                nodata=float(tags['42113']),width=width,height=height,
                resampling=resampling,model_eligible=resampling=='NEAREST')


def acquire(record, output):
    target=output/'frame.bin'
    proof=output/'frame.json'
    if target.exists():
        receipt=json.loads(proof.read_text())
        if hashlib.sha256(target.read_bytes()).hexdigest()!=receipt['sha256']:
            raise ValueError('Coarse frame cache hash changed')
        return receipt
    url=record['source_records'][1]['url']
    start,stop=record['start'],record['stop']
    with urlopen(Request(url,headers={'Range':f'bytes={start}-{stop-1}'}),timeout=90) as response:
        expected=f"bytes {start}-{stop-1}/{record['source_records'][1]['size_bytes']}"
        if response.status!=206 or response.headers.get('Content-Range')!=expected:
            raise ValueError('Source declined exact bounded frame range')
        body=response.read(stop-start+1)
    if len(body)!=stop-start:
        raise ValueError('Incomplete coarse pixel range')
    receipt=dict(url=url,retrieved_utc=datetime.now(timezone.utc).isoformat(),
        content_range=expected,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    target.write_bytes(body)
    write(proof,receipt)
    print(f"Downloaded coarse frame: {record['name']} ({len(body):,} bytes)",flush=True)
    return receipt


def standalone_frame(record, cache, output):
    """Repack one coarse page so libtiff never reads the large parent file.

    Compressed tile bytes remain identical; only header/offset tables move.
    BigTIFF preserves both endian orders and signed sample metadata.
    """
    stream=RangeReader(record['source_records'][1]['url'],
                      cache/(record['name']+'.ovr'),budget=1_000_000)
    header=Header(stream)
    body=(output/'frame.bin').read_bytes()
    proof=json.loads((output/'frame.json').read_text())
    if hashlib.sha256(body).hexdigest()!=proof['sha256']:
        raise ValueError('Pixel range hash changed')
    entries,_=header.directory(record['frame']['ifd_offset'])
    if 330 in entries:
        raise ValueError('SubIFD pointers require a separate repacking review')
    sizes={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4,16:8,17:8,18:8}
    fields={}
    offset_tag=324 if 324 in entries else 273
    old_offsets=header.value(entries[offset_tag])
    old_offsets=[old_offsets] if isinstance(old_offsets,int) else old_offsets
    for tag,(kind,n,inline) in entries.items():
        length=n*sizes[kind]
        if length>1_000_000:
            raise ValueError('Coarse metadata field exceeds byte cap')
        raw=inline[:length] if length<=header.inline_size else header.read_at(
            struct.unpack(header.order+header.pointer,inline)[0],length)
        fields[tag]=(kind,n,raw)
    fields[offset_tag]=(16,len(old_offsets),b'\0'*(8*len(old_offsets)))
    cursor=16+8+20*len(fields)+8
    positions={}
    for tag,(_,_,raw) in sorted(fields.items()):
        if len(raw)>8:
            cursor=(cursor+7)//8*8
            positions[tag]=cursor
            cursor+=len(raw)
    pixel_start=(cursor+7)//8*8
    moved=[pixel_start+value-record['start'] for value in old_offsets]
    fields[offset_tag]=(16,len(moved),struct.pack(header.order+str(len(moved))+'Q',*moved))
    result=bytearray(pixel_start)
    result[:16]=(b'II' if header.order=='<' else b'MM')+struct.pack(header.order+'HHHQ',43,8,0,16)
    result[16:24]=struct.pack(header.order+'Q',len(fields))
    for index,(tag,(kind,n,raw)) in enumerate(sorted(fields.items())):
        value=raw.ljust(8,b'\0') if len(raw)<=8 else struct.pack(header.order+'Q',positions[tag])
        entry=struct.pack(header.order+'HHQ',tag,kind,n)+value
        result[24+20*index:44+20*index]=entry
        if len(raw)>8:
            result[positions[tag]:positions[tag]+len(raw)]=raw
    result.extend(body)
    return io.BytesIO(result)
