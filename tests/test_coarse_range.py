"""Ensure virtual TIFF reads the selected coarse page with exact signed values."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from scripts.context.tiff_metadata import Header
from scripts.context.coarse_range import standalone_frame


class FakeRange(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.size=len(body)


class CoarseTests(unittest.TestCase):
    def test_signed_pixels_and_selected_ifd(self):
        full=np.arange(4096,dtype=np.int16).reshape(64,64)-1000
        coarse=full[::2,::2].copy()
        coarse[0,0]=-32768
        buffer=io.BytesIO()
        Image.fromarray(full).save(buffer,format='TIFF',save_all=True,
            append_images=[Image.fromarray(coarse)],compression='tiff_adobe_deflate')
        body=buffer.getvalue()
        header=Header(io.BytesIO(body))
        frame=list(header.frames())[1]
        entries,_=header.directory(frame['ifd_offset'])
        offsets=header.value(entries[273])
        counts=header.value(entries[279])
        offsets=[offsets] if isinstance(offsets,int) else offsets
        counts=[counts] if isinstance(counts,int) else counts
        start=min(offsets);stop=max(a+b for a,b in zip(offsets,counts))
        record=dict(name='fixture',frame=frame,start=start,stop=stop,
                    source_records=[{},dict(url='fixture')])
        with tempfile.TemporaryDirectory() as path:
            out=Path(path)
            payload=body[start:stop]
            (out/'frame.bin').write_bytes(payload)
            (out/'frame.json').write_text(json.dumps(dict(sha256=hashlib.sha256(payload).hexdigest())))
            with patch('scripts.context.coarse_range.RangeReader',return_value=FakeRange(body)):
                stream=standalone_frame(record,out,out)
                with Image.open(stream) as image:
                    self.assertEqual(image.size,(32,32))
                    np.testing.assert_array_equal(np.array(image),coarse)


if __name__=='__main__':
    unittest.main()
