import unittest

import numpy as np

from klang.music.chords import invert_chord


class TestChordInversion(unittest.TestCase):
    def test_invert_chord(self):
        MAJOR = np.array([0, 4, 7])

        # No inversion
        np.testing.assert_equal(invert_chord(MAJOR, inversion=0), MAJOR)

        # Up
        np.testing.assert_equal(invert_chord(MAJOR, inversion=1), [4, 7, 12])
        np.testing.assert_equal(invert_chord(MAJOR, inversion=2), [7, 12, 16])

        # Down
        np.testing.assert_equal(invert_chord(MAJOR, inversion=-1), [-5, 0, 4])
        np.testing.assert_equal(invert_chord(MAJOR, inversion=-2), [-8, -5, 0])


if __name__ == '__main__':
    unittest.main()
