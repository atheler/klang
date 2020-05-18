import unittest

import numpy as np

from klang.audio.helpers import get_silence, get_time


class TestCachedSignals(unittest.TestCase):
    def test_read_only(self):
        for func in [get_silence, get_time]:
            arr = func(10)
            with self.assertRaises(ValueError):
                arr[0] = 666

    def test_silence(self):
        """Test silence array. Mono and stereo."""
        mono = get_silence(10)

        np.testing.assert_equal(mono, np.zeros(10))

        stereo = get_silence((2, 10))

        np.testing.assert_equal(stereo, np.zeros((2, 10)))

    def test_time(self):
        """Test time array."""
        t = get_time(10, .1)

        np.testing.assert_equal(t, .1 * np.arange(10))


if __name__ == '__main__':
    unittest.main()
