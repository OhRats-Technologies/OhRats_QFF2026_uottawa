"""Read selected TIFF tags without loading enormous native tile-offset arrays.

Classic/BigTIFF layouts follow libtiff's public specification. Pixel decoding
remains Pillow/GDAL's job; this reader only locates bounded metadata and frames.
"""
import struct

FORMATS = {1:'B',2:'c',3:'H',4:'I',6:'b',7:'B',8:'h',9:'i',11:'f',12:'d',13:'I',16:'Q',17:'q',18:'Q'}
SELECTED = {256,257,258,259,262,277,278,284,317,322,323,339,33550,33922,34735,34736,34737,42112,42113}


class Header:
    def __init__(self, stream):
        self.stream = stream
        raw = self.read_at(0,16)
        self.order = {b'II':'<',b'MM':'>'}[raw[:2]]
        magic = struct.unpack(self.order+'H',raw[2:4])[0]
        if magic == 43:
            assert struct.unpack(self.order+'HH',raw[4:8]) == (8,0)
            self.big = True
        elif magic == 42:
            self.big = False
        else:
            raise ValueError('Not a supported TIFF header')
        self.pointer = 'Q' if self.big else 'I'
        self.inline_size = 8 if self.big else 4
        self.first_ifd = struct.unpack(self.order+self.pointer,raw[8:16] if self.big else raw[4:8])[0]

    def read_at(self, offset, count):
        self.stream.seek(offset)
        body = self.stream.read(count)
        if len(body) != count:
            raise ValueError('Incomplete TIFF metadata range')
        return body

    def directory(self, offset):
        size = 8 if self.big else 2
        count = struct.unpack(self.order+('Q' if self.big else 'H'),self.read_at(offset,size))[0]
        if count > 256:
            raise ValueError('Unexpected number of raster tags')
        entry_size = 20 if self.big else 12
        raw = self.read_at(offset+size,count*entry_size+self.inline_size)
        entries = {}
        for index in range(count):
            row = raw[index*entry_size:(index+1)*entry_size]
            tag,kind,n = struct.unpack(self.order+('HHQ' if self.big else 'HHI'),row[:-self.inline_size])
            entries[tag] = (kind,n,row[-self.inline_size:])
        next_ifd = struct.unpack(self.order+self.pointer,raw[-self.inline_size:])[0]
        return entries,next_ifd

    def value(self, entry):
        kind,n,inline = entry
        code = FORMATS[kind]
        count = n*struct.calcsize(code)
        if count > 1_000_000:
            raise ValueError('Selected metadata field exceeds byte cap')
        raw = inline[:count] if count <= self.inline_size else self.read_at(
            struct.unpack(self.order+self.pointer,inline)[0],count)
        if kind == 2:
            return raw.rstrip(b'\0').decode('utf-8')
        values = struct.unpack(self.order+str(n)+code,raw)
        return values[0] if n == 1 else list(values)

    def frames(self):
        offset = self.first_ifd
        seen = set()
        while offset:
            if offset in seen or len(seen) >= 16:
                raise ValueError('Invalid TIFF frame chain')
            seen.add(offset)
            entries,next_ifd = self.directory(offset)
            tags = {str(tag):self.value(entry) for tag,entry in entries.items() if tag in SELECTED}
            yield dict(ifd_offset=offset,tags=tags)
            offset = next_ifd
