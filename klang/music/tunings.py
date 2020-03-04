"""All things related to tuning.

Conversion functions, temperaments.

Resources:
  - http://www.wolfgang-wiese.de/Historische%20Stimmungen-Schwebungen.pdf.
"""
import numpy as np

from config import KAMMERTON
from klang.constants import DODE, REF_OCTAVE
from klang.music.pitch import pitch_2_frequency, pitch_2_note_name
from klang.util import load_music_data_from_csv, find_item


CENT_PER_OCTAVE = 1200
"""int: Cents per octave. TODO(atheler): To be moved to klang.constants?"""

OCTAVE = 2.
"""float: Octave frequency ratio. TODO(atheler): To be moved to klang.constants?"""

KAMMERTON_OFFSET = 9
"""int: Kammerton pitch offset (not in use at the moment?)."""

EQUAL_TEMPERAMENT = None
"""Temperament: Default equal temperament."""

TEMPERAMENTS = {}
"""dict: Name (str) -> Temperament (Temperament)."""

TUNINGS_FILEPATH = 'resources/tunings.csv'
"""str: CSV filepath for additional tunings."""

RATIOS = {
    'Equal': 2. ** (np.arange(DODE) / DODE),
    'Young': [
        1., 1.055730636, 1.119771437, 1.187696971, 1.253888072, 1.334745462,
        1.407640848, 1.496510232, 1.583595961, 1.675749414, 1.781545449,
        1.878842233
    ],
    'Pythagorean': [
        1., 12./11., 9./8., 6./5., 5./4., 4./3., 7./5., 3./2., 8./5., 5./3.,
        7./4., 11./6.
    ],
    'Random': 1. + np.sort(np.random.random(DODE)),
}

RATIOS.update(load_music_data_from_csv(TUNINGS_FILEPATH))
"""dict: Temperament name (str) -> Frequency ratios."""


def find_temperament(name):
    """Look for temperament."""
    return find_item(TEMPERAMENTS, name)


def ratio_2_cent(ratio):
    """Convert frequency ratio to cent."""
    return CENT_PER_OCTAVE * np.log2(ratio)


assert ratio_2_cent(OCTAVE) == CENT_PER_OCTAVE


def cent_2_ratio(cent):
    """Convert cent to frequency ratio."""
    return 2 ** (cent / CENT_PER_OCTAVE)


assert cent_2_ratio(CENT_PER_OCTAVE) == OCTAVE


class Temperament:

    """Tuning temperament."""

    def __init__(self, name, ratios, kammerton=KAMMERTON):
        """Args:
            name (str): Name of the temperament.
            ratios (array): Frequency ratios. At the moment only length-12 are
                supported and first frequency ratio has to be 1.0!
        Kwargs:
            kammerton (frequency): Reference pitch for A4 (or A3 in MIDI).
        """
        assert len(ratios) == DODE
        self.name = name
        self.ratios = np.asarray(ratios, dtype=float)
        self.kammerton = kammerton
        self.refFrequency = pitch_2_frequency(60, kammerton)

    def pitch_2_frequency(self, pitch):
        octave, note = np.divmod(pitch, DODE)
        return self.refFrequency * self.ratios[note] * (2. ** (octave - REF_OCTAVE))

    def frequency_2_pitch(self, frequency):
        raise NotImplementedError
        # TODO(atheler): Do we need this?

    def __str__(self):
        return '%s(%r, %.1f Hz)' % (
            self.__class__.__name__,
            self.name,
            self.kammerton,
        )


EQUAL_TEMPERAMENT = Temperament('Equal', 2. ** (np.arange(DODE) / DODE))


def _init_temperaments():
    global TEMPERAMENTS
    for name, ratios in RATIOS.items():
        TEMPERAMENTS[name] = Temperament(name, ratios)


_init_temperaments()


if __name__ == '__main__':
    kammerton = 442.
    ratios = 2. ** (np.arange(DODE) / DODE)
    EQUAL_TEMPERAMENT = Temperament('Equal', ratios, kammerton=kammerton)

    print(EQUAL_TEMPERAMENT)
    print('Pitch 60 ->', EQUAL_TEMPERAMENT.pitch_2_frequency(60))
    print('Pitch 69 ->', EQUAL_TEMPERAMENT.pitch_2_frequency(69))

    for pitch in range(60, 72):
        print(pitch, '->', pitch_2_note_name(pitch))
