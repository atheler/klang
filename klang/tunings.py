import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

from config import KAMMERTON
from klang.constants import DODE, REF_OCTAVE


def frequency_2_pitch(frequency, kammerton=KAMMERTON):
    """Frequency to MIDI note number (equal temperament)."""
    return 69 + 12 * np.log2(frequency / kammerton)


assert frequency_2_pitch(KAMMERTON) == 69


def pitch_2_frequency(noteNumber, kammerton=KAMMERTON):
    """MIDI note number to frequency (equal temperament)."""
    return (2 ** ((noteNumber - 69) / 12)) * kammerton


assert pitch_2_frequency(69) == KAMMERTON






def find_base_frequency():
    # TODO(atheler): Find better approximation of base / reference frequency
    pass


class Temperament:

    """Tuning temperament."""

    refRatioIdx = 9  # Only for dode

    def __init__(self, name, ratios, kammerton=KAMMERTON):
        assert len(ratios) == DODE and ratios[0] == 1.
        self.name = name
        self.ratios = np.asarray(ratios, dtype=float)
        self.kammerton = kammerton

    @property
    def base_frequency(self):
        return self.kammerton / self.ratios[self.refRatioIdx]

    def pitch_2_frequency(self, pitch):
        octave, note = np.divmod(pitch, DODE)
        return self.base_frequency * self.ratios[note] * (2 ** (octave - REF_OCTAVE))

    def frequency_2_pitch(self, frequency):
        raise NotImplementedError
        # Round to nearest pitch(es)

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self.name)




ratios = 2. ** (np.arange(DODE) / DODE)

EQUAL_TEMPERAMENT = Temperament('Equal', ratios)
print(EQUAL_TEMPERAMENT)
print(EQUAL_TEMPERAMENT.pitch_2_frequency(60))
print(EQUAL_TEMPERAMENT.pitch_2_frequency(69))
