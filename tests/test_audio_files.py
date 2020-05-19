import unittest

import numpy as np

from klang.audio.wavfile import convert_samples_to_float, convert_samples_to_int


class TestSampleConversion(unittest.TestCase):
    def test_convert_samples_to_float(self):
        np.testing.assert_equal(
            convert_samples_to_float(np.array([-32768, 0], dtype=np.int16)),
            np.array([-1., 0.]),
        )

    def test_convert_samples_to_int(self):
        np.testing.assert_equal(
            convert_samples_to_int(np.array([-1., 0., 1.])),
            np.array([-32767, 0, 32767], dtype=np.int16),
        )


if __name__ == '__main__':
    unittest.main()
