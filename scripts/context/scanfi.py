"""Inspect advertised SCANFI GeoTIFF layout with a strict ranged-byte budget."""
import argparse
import hashlib
import io
import json
import re
from threading import Lock
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from PIL import Image

BASE = 'https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2/'
HEADER_LOCK = Lock()


class RangeReader(io.RawIOBase):
    def __init__(self, url, cache, budget=4_000_000):
        self.url, self.cache, self.budget = url, cache, budget
        self.position = 0
        self.receipts = []
        self.blocks = {}
        self.cache.mkdir(parents=True, exist_ok=True)
        self._fetch(0)

    def _fetch(self, start):
        target = self.cache / f'{start}.bin'
        receipt_path = target.with_suffix('.json')
        if target.exists():
            body = target.read_bytes()
            receipt = json.loads(receipt_path.read_text())
            if hashlib.sha256(body).hexdigest() != receipt['sha256']:
                raise ValueError('Cached range hash mismatch')
        else:
            consumed = sum(len(b) for b in self.blocks.values())
            if consumed + 65536 > self.budget:
                raise ValueError('4 MB ranged metadata budget exhausted')
            headers = {'Range': f'bytes={start}-{start + 65535}'}
            with urlopen(Request(self.url, headers=headers), timeout=20) as response:
                content_range = response.headers.get('Content-Range', '')
                if response.status != 206 or not content_range.startswith(f'bytes {start}-'):
                    raise ValueError('Source does not honor byte ranges; full download declined')
                body = response.read(65537)
                if len(body) > 65536:
                    raise ValueError('Range response exceeds requested block')
            receipt = {'url': self.url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                       'content_range': content_range, 'sha256': hashlib.sha256(body).hexdigest()}
            target.write_bytes(body)
            receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        self.size = int(receipt['content_range'].split('/')[-1])
        self.blocks[start] = body
        self.receipts.append(receipt)
        return body

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        return self.position

    def read(self, count=-1):
        if count < 0:
            count = self.size - self.position
        if count > self.budget:
            raise ValueError('Unbounded TIFF read declined')
        stop = min(self.size, self.position + count)
        parts = []
        while self.position < stop:
            start = self.position // 65536 * 65536
            block = self.blocks.get(start) or self._fetch(start)
            offset = self.position - start
            part = block[offset:min(len(block), offset + stop - self.position)]
            if not part:
                break
            parts.append(part)
            self.position += len(part)
        return b''.join(parts)


def inspect(url, cache):
    record = {'url': url, 'purpose': 'layout/metadata only; no pixels or model fitting'}
    reader = None
    try:
        reader = RangeReader(url, cache)
        # Only parse tags under the ranged-byte cap; never decode national pixels.
        with HEADER_LOCK:
            original_pixel_limit = Image.MAX_IMAGE_PIXELS
            try:
                Image.MAX_IMAGE_PIXELS = None
                image = Image.open(reader)
            finally:
                Image.MAX_IMAGE_PIXELS = original_pixel_limit
        tags = image.tag_v2
        record.update(status='inspected', size_bytes=reader.size,
                      width=image.width, height=image.height, mode=image.mode,
                      compression=tags.get(259), tile_width=tags.get(322),
                      tile_height=tags.get(323), rows_per_strip=tags.get(278),
                      model_pixel_scale=tags.get(33550), model_tiepoint=tags.get(33922),
                      geo_keys=tags.get(34735), nodata=tags.get(42113),
                      geo_double_params=tags.get(34736), geo_ascii_params=tags.get(34737),
                      gdal_metadata=tags.get(42112),
                      sub_ifds=tags.get(330))
    except Exception as error:
        record.update(status='not_inspected', error=str(error))
    if reader:
        record['retrieved_bytes'] = sum(len(b) for b in reader.blocks.values())
        record['requests'] = reader.receipts
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    args = parser.parse_args()
    directory = (args.cache / 'guides/scanfi-directory.raw').read_text()
    links = re.findall(r'href="([^"]+)"', directory)
    names = ['SCANFI_att_height_1990_v2_20260119.tif', 'SCANFI_att_height_2015_v2_20260119.tif']
    records = []
    for name in names:
        if name not in links:
            raise ValueError('Filename was not advertised by the retrieved directory')
        for resource in [name, name + '.ovr']:
            if resource in links:
                records.append(inspect(urljoin(BASE, resource), args.cache / 'scanfi' / resource))
    output = {'catalogue': 'https://open.canada.ca/data/en/dataset/07653869-f303-46c2-a04e-9ab479b73cbf',
              'note': 'Ranged metadata layout check, not numerical Ontario extraction or predictive improvement.',
              'records': records}
    Path('docs/data/scanfi_access.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps([{k: r.get(k) for k in ['url', 'status', 'size_bytes', 'retrieved_bytes', 'error']} for r in records], indent=2))
