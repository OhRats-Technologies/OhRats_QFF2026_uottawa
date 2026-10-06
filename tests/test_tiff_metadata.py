"""Check sparse classic/BigTIFF metadata against GDAL and skip giant arrays."""
import io
import struct
import unittest
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from scripts.context.tiff_metadata import Header


class MetadataTests(unittest.TestCase):
    def test_matches_gdal_classic_and_bigtiff(self):
        for big in ['YES','NO']:
            with self.subTest(big=big), MemoryFile() as mem:
                with mem.open(driver='GTiff',width=64,height=48,count=1,dtype='uint16',
                              crs='EPSG:4326',transform=from_origin(-95,57,.01,.01),
                              nodata=65535,BIGTIFF=big,tiled=True,blockxsize=16,blockysize=16) as ds:
                    ds.write(np.zeros((48,64),dtype='uint16'),1)
                tags=next(Header(io.BytesIO(mem.read())).frames())['tags']
                self.assertEqual(tags['256'],64)
                self.assertEqual(tags['257'],48)
                self.assertEqual(tags['42113'],'65535')
                self.assertEqual(tags['33550'],[.01,.01,0.])
                self.assertEqual(tags['33922'],[0.,0.,0.,-95.,57.,0.])

    def test_does_not_read_huge_offset_table(self):
        # A valid directory advertises a huge TileOffsets table far beyond EOF.
        # Selected tags can still be inspected without materializing that table.
        for order,mark in [('<',b'II'),('>',b'MM')]:
            header=mark+struct.pack(order+'HHHQ',43,8,0,16)
            entries=[struct.pack(order+'HHQQ',256,4,1,64),
                     struct.pack(order+'HHQQ',257,4,1,48),
                     struct.pack(order+'HHQQ',324,16,1_000_000_000,1_000_000)]
            body=header+struct.pack(order+'Q',3)+b''.join(entries)+struct.pack(order+'Q',0)
            # SHORT/LONG inline bytes must be endian-appropriate within 8 bytes.
            if order == '>':
                entries[:2]=[struct.pack(order+'HHQ',tag,4,1)+struct.pack(order+'I',v)+b'\0'*4
                             for tag,v in [(256,64),(257,48)]]
                body=header+struct.pack(order+'Q',3)+b''.join(entries)+struct.pack(order+'Q',0)
            frames=list(Header(io.BytesIO(body)).frames())
            self.assertEqual(frames[0]['tags'],{'256':64,'257':48})


if __name__ == '__main__':
    unittest.main()
