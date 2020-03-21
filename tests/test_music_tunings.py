import unittest

import numpy as np

from klang.music.tunings import (
    ratio_2_cent, cent_2_ratio, Temperament
)
from klang.constants import CENT_PER_OCTAVE

OCTAVE = 2.
"""float: Octave frequency ratio. TODO(atheler): To be moved to klang.constants?"""


assert ratio_2_cent(OCTAVE) == CENT_PER_OCTAVE
assert cent_2_ratio(CENT_PER_OCTAVE) == OCTAVE


class TestTemperament(unittest.TestCase):
    def test_pitch_2_frequency(self):
        equalTuning = np.arange(12) * 100
        equal = Temperament(equalTuning, kammerton=440.)
        self.assertAlmostEqual(equal.pitch_2_frequency(69), 440.)
        self.assertAlmostEqual(equal.pitch_2_frequency(69 + 12), 880.)

    def test_with_different_kammerton(self):
        kammerton = 435.23
        equalTuning = np.arange(12) * 100
        equal = Temperament(equalTuning, kammerton=kammerton)
        self.assertAlmostEqual(equal.pitch_2_frequency(69), kammerton)
        self.assertAlmostEqual(equal.pitch_2_frequency(69 + 12), 2*kammerton)


if __name__ == '__main__':
    unittest.main()
