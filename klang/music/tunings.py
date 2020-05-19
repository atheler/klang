"""All things related to tuning.

Conversion functions, temperaments.

Resources:
  - http://www.wolfgang-wiese.de/Historische%20Stimmungen-Schwebungen.pdf.
"""
import pkgutil

import numpy as np

from klang.config import KAMMERTON
from klang.constants import DODE, REF_OCTAVE, CENT_PER_OCTAVE
from klang.util import parse_music_data_from_csv, find_item


__all__ = [
    'TEMPERAMENTS', 'EQUAL_TEMPERAMENT', 'ratio_2_cent', 'cent_2_ratio',
    'find_temperament', 'Temperament',
]


TEMPERAMENTS = {}
"""dict: Name (str) -> Temperament (Temperament)."""

KAMMERTON_OFFSET = 9
"""int: Kammerton pitch offset (not in use at the moment?)."""

EQUAL_TEMPERAMENT = None
"""Temperament: Default tuning temperament."""


def ratio_2_cent(ratio):
    """Convert frequency ratio to cent."""
    return CENT_PER_OCTAVE * np.log2(ratio)


def cent_2_ratio(cent):
    """Convert cent to frequency ratio."""
    return 2 ** (cent / CENT_PER_OCTAVE)


def find_temperament(name):
    """Find temperament by name."""
    return find_item(TEMPERAMENTS, name)


class Temperament:

    """Tuning temperament."""

    def __init__(self, cents, kammerton=KAMMERTON, name=''):
        """Args:
            cents (array): Tuning.
        Kwargs:
            kammerton (frequency): Reference pitch for A4 (or A3 in MIDI).
        """
        assert len(cents) == DODE
        self.kammerton = kammerton
        self.name = name

        cents = np.asarray(cents)
        self.ratios = cent_2_ratio(cents)
        self.baseFrequency = kammerton / self.ratios[KAMMERTON_OFFSET]

    def pitch_2_frequency(self, pitch):
        """Convert pitch number to frequency value."""
        octave, note = np.divmod(pitch, DODE)
        return self.baseFrequency * self.ratios[note] * (2. ** (octave - REF_OCTAVE))

    def __str__(self):
        infos = []
        if self.name:
            infos.append('%r' % self.name)

        infos.append(
            'kammerton: %.1f Hz' % self.kammerton
        )

        return '%s(%s)' % (type(self).__name__, ', '.join(infos))


def _init_temperaments():
    youngRatios = [
        1., 1.055730636, 1.119771437, 1.187696971, 1.253888072, 1.334745462,
        1.407640848, 1.496510232, 1.583595961, 1.675749414, 1.781545449,
        1.878842233,
    ]
    pythagoreanRatios = [
        1, 12/11, 9/8, 6/5, 5/4, 4/3, 7/5, 3/2, 8/5, 5/3, 7/4, 11/6,
    ]
    justIntonation = [
        1, 16/15, 9/8, 6/5, 5/4, 4/3, 45/32, 3/2, 8/5, 5/3, 9/5, 15/8,
    ]
    rnd = np.sort(np.random.randint(0, CENT_PER_OCTAVE, size=12))
    temperaments = {
        'Equal': EQUAL_TEMPERAMENT,
        'Young': Temperament(ratio_2_cent(youngRatios), name='Young'),
        'Pythagorean': Temperament(ratio_2_cent(pythagoreanRatios), name='Pythagorean'),
        'Just': Temperament(ratio_2_cent(justIntonation), name='Just'),
        'Random': Temperament(rnd, name='Random'),
    }

    # Load remaing temperaments from tunings.csv
    data = pkgutil.get_data('klang.music', 'data/tunings.csv')
    for name, cents in parse_music_data_from_csv(data).items():
        temperaments[name.title().strip()] = Temperament(cents, name=name)

    return temperaments


EQUAL_TEMPERAMENT = Temperament(np.arange(DODE)*100, kammerton=KAMMERTON, name='Equal')
TEMPERAMENTS['Equal'] = EQUAL_TEMPERAMENT
TEMPERAMENTS.update(_init_temperaments())
