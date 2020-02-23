"""Tuning temperaments.

Resources:
  - https://www.earmaster.com/fr/music-theory-online/ch06/chapter-6-2.html
  - https://en.wikipedia.org/wiki/Meantone_temperament
  - https://en.wikipedia.org/wiki/Pythagorean_tuning
"""
import numpy as np

from rhesuton.constants import DODE, REF_OCTAVE
from rhesuton.midi import pitch_2_frequency


FREQUENCIES_RATIOS = {
    'Equal': np.power(2., np.arange(DODE) / DODE),
    'Young': np.array([
        1., 1.055730636, 1.119771437, 1.187696971, 1.253888072, 1.334745462,
        1.407640848, 1.496510232, 1.583595961, 1.675749414, 1.781545449,
        1.878842233,
    ]),
    'Pythagorean': np.array([
        1., 12./11., 9./8., 6./5., 5./4., 4./3., 7./5., 3./2., 8./5., 5./3.,
        7./4., 11./6.,
    ]),
    'Random': 1. + np.sort(np.random.random(DODE)),
}
"""dict: Temperament name (str) -> Frequency ratios (array)."""


class Temperament:

    """Tuning temperament. Given the tuning of the reference octave maps note
    numbers to frequencies.

    TODO(atheler): Rework!
      - Non dodo temperaments (e.g. 24-TET, Indian, Chinese).
      - Frequency ratios vs. cents.
      - Kammerton / reference pitch in constructor
      - Helper methods: pitch_to_frequency(pitch) instead of __call__()
      - Signal support? Inputs for Kammerton? Ratios?
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


C4 = pitch_2_frequency(60)
"""float: Reference base c frequency."""

TEMPERAMENTS = {}
"""dict: Temperament name (str) -> Temperament."""

for name, ratios in FREQUENCIES_RATIOS.items():
    TEMPERAMENTS[name] = Temperament.from_ratios(name, C4, ratios)


def get_temperament_by_name(name):
    """Load temperament by name."""
    return TEMPERAMENTS[name]
