"""Independent zlib/NumPy tile decoding against saved Pillow-derived Ontario pixels."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zlib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.context.tiff_metadata import Header


class CachedHeader(io.RawIOBase):
    """Use existing source bytes only; a missing block is an error, never a request."""
    def __init__(self, directory):
        self.directory, self.position = directory, 0

    def seek(self, position, whence=0):
        assert whence == 0
        self.position = position
        return position

    def tell(self):
        return self.position

    def read(self, count):
        output = bytearray()
        while count:
            block_start = self.position//65536*65536
            path = self.directory/f'{block_start}.bin'
            body = path.read_bytes()
            proof = json.loads(path.with_suffix('.json').read_text())
            assert hashlib.sha256(body).hexdigest() == proof['sha256']
            offset = self.position-block_start
            amount = min(count, len(body)-offset)
            assert amount > 0
            output.extend(body[offset:offset+amount])
            count -= amount
            self.position += amount
        return bytes(output)


def decode(payload, tags, order):
    assert tags['259'] == 8 and tags['277'] == 1
    bits, width, height = tags['258'], tags['322'], tags['323']
    assert bits in [8, 16]
    unsigned = np.dtype(order+f'u{bits//8}')
    values = np.frombuffer(zlib.decompress(payload), dtype=unsigned).reshape(height, width)
    predictor = tags.get('317', 1)
    assert predictor in [1, 2]
    if predictor == 2:
        values = np.cumsum(values, axis=1, dtype=np.uint64).astype(unsigned)
    if tags.get('339', 1) == 2:
        values = values.view(np.dtype(order+f'i{bits//8}'))
    return values


def audit(root):
    base = root/'.cache/context/forest-features-v2/resources'
    records = []
    for path in sorted(base.glob('*/layout.json')):
        record = json.loads(path.read_text())
        if record['epoch'] not in [1985, 2015]:
            continue
        directory = path.parent
        proof = json.loads((directory/'frame.json').read_text())
        pixels = (directory/'frame.bin').read_bytes()
        assert hashlib.sha256(pixels).hexdigest() == proof['sha256']
        header_root = root/'.cache/context/forest-selective-layout-v1'/(record['name']+'.ovr')
        header = Header(CachedHeader(header_root))
        entries, _ = header.directory(record['frame']['ifd_offset'])
        offsets = np.atleast_1d(header.value(entries[324])).tolist()
        counts = np.atleast_1d(header.value(entries[325])).tolist()
        tags = record['frame']['tags']
        with np.load(directory/'ontario.npz') as saved:
            array, valid, affine = saved['values'], saved['valid'], saved['transform']
        native = record['source_records'][0]['frames'][0]['tags']
        origin = native['33922']
        pixel = native['33550'][0]*record['factor']
        row_start = round((origin[4]-affine[5])/pixel)
        column_start = round((affine[2]-origin[3])/pixel)
        tile_width, tile_height = tags['322'], tags['323']
        columns = (record['width']+tile_width-1)//tile_width
        valid_positions = np.flatnonzero(valid)
        points = valid_positions[[int((len(valid_positions)-1)*q) for q in [.1, .5, .9]]]
        tiles = set()
        for point in points:
            row, column = np.unravel_index(point, valid.shape)
            tiles.add(((row_start+row)//tile_height, (column_start+column)//tile_width))
        checked = []
        for tile_row, tile_column in sorted(tiles):
            index = tile_row*columns+tile_column
            offset, length = offsets[index]-record['start'], counts[index]
            block = decode(pixels[offset:offset+length], tags, header.order)
            r0, c0 = tile_row*tile_height-row_start, tile_column*tile_width-column_start
            first_row, last_row = max(r0, 0), min(r0+tile_height, array.shape[0])
            first_col, last_col = max(c0, 0), min(c0+tile_width, array.shape[1])
            expected = array[first_row:last_row, first_col:last_col]
            actual = block[first_row-r0:last_row-r0, first_col-c0:last_col-c0]
            np.testing.assert_array_equal(actual, expected)
            checked.append(dict(tile_row=int(tile_row), tile_column=int(tile_column),
                                pixels=int(actual.size), mismatches=0,
                                signed_minimum=int(actual.min()), maximum=int(actual.max())))
        records.append(dict(layer=record['layer'], epoch=record['epoch'], source_url=proof['url'],
                            source_frame_sha256=proof['sha256'],
                            saved_roi_sha256=hashlib.sha256((directory/'ontario.npz').read_bytes()).hexdigest(),
                            sample_format=tags.get('339', 1), bits=tags['258'],
                            overview_eligible=record['model_eligible'], tiles=checked))
    assert len(records) == 12
    return dict(status='passed', sources=12, tiles=sum(len(r['tiles']) for r in records),
                pixels=sum(t['pixels'] for r in records for t in r['tiles']), mismatches=0,
                network_requests=0, shared='Cached TIFF header parser and existing ROI transform/masks.',
                independent='Deflate codec and signed/horizontal-predictor decoding use zlib/NumPy, not Pillow/libtiff.',
                limitation='Bounded decoder spot check, not all42 full arrays or an independent spatial-boundary audit. Excluded2015 age remains excluded.',
                records=records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['status', 'sources', 'tiles', 'pixels', 'mismatches']}))
