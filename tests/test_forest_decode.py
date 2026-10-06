"""Independent byte decoder retains nodata, valid zero and signed values."""
import unittest
import zlib
import numpy as np
from scripts.context.forest_decode_audit import decode


class DecodeTests(unittest.TestCase):
    def test_signed_deflate_and_horizontal_predictor(self):
        expected = np.array([[-32768, 0, 127, 32767], [2, 0, -4, 8]], dtype='<i2')
        for predictor in [1, 2]:
            values = expected.view('<u2').copy()
            if predictor == 2:
                values[:, 1:] = np.diff(values.astype(np.int64), axis=1).astype('<u2')
            tags = {'259': 8, '277': 1, '258': 16, '322': 4, '323': 2,
                    '317': predictor, '339': 2}
            actual = decode(zlib.compress(values.tobytes()), tags, '<')
            np.testing.assert_array_equal(actual, expected)


if __name__ == '__main__':
    unittest.main()
