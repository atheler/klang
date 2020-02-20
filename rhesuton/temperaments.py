import numpy as np

from rhesuton.constants import DODE, REF_OCTAVE
from rhesuton.midi import pitch_2_frequency


EQUAL_TEMPERAMENT_RATIOS = np.power(2., np.arange(DODE) / DODE)
THOMAS_YOUNG_TEMPERAMENT_RATIOS = np.array([
    1, 1.055730636, 1.119771437, 1.187696971, 1.253888072, 1.334745462,
    1.407640848, 1.496510232, 1.583595961, 1.675749414, 1.781545449,
    1.878842233,
])


class Temperament:

    """Tuning temperament. Given the tuning of the reference octave maps note
    numbers to frequencies.
    """

    def __init__(self, name, frequencies):
        """Args:
            frequencies (array): Frequencies of reference octave.
        """
        assert len(frequencies) == DODE, 'We need twelve notes!'

        self.name = name
        self.frequencies = np.asarray(frequencies, dtype=float)

    @classmethod
    def from_ratios(cls, name, baseFreq, ratios):
        assert len(ratios) == DODE
        frequencies = baseFreq * ratios
        return cls(name, frequencies)

    def __call__(self, pitch):
        """Map note numbers / pitches to frequencies."""
        octave, note = np.divmod(pitch, DODE)
        return self.frequencies[note] * (2 ** (octave - REF_OCTAVE))

    def __str__(self):
        return '%s(name=%r, %.3f Hz to %.3f Hz)' % (
            self.__class__.__name__,
            self.name,
            self.frequencies.min(),
            self.frequencies.max(),
        )


c0 = pitch_2_frequency(60)
EQUAL_TEMPERAMENT = Temperament.from_ratios('Equal', c0, EQUAL_TEMPERAMENT_RATIOS)
YOUNG_TEMPERAMENT = Temperament.from_ratios('Young', c0, THOMAS_YOUNG_TEMPERAMENT_RATIOS)


TEMPERAMENTS = {
    'Equal': EQUAL_TEMPERAMENT,
    'Young': YOUNG_TEMPERAMENT,
}


def get_temperament_by_name(name):
    """Load temperament by name."""
    return TEMPERAMENTS[name]
