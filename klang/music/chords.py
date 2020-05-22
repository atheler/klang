"""Music chords."""
import pkgutil

import numpy as np

from klang.constants import SEMITONES_PER_OCTAVE
from klang.util import find_item, parse_music_data_from_csv


__all__ = ['CHORDS', 'find_chord', 'invert_chord']


CHORDS = {}
"""dict: Chord name (str) -> Chord mapping (array)."""


def find_chord(name):
    """Find chord in database."""
    return find_item(CHORDS, name)


def _invert_up(chord):
    """Invert chord up. Helper for invert_chord()."""
    lowest, *core = chord
    return core + [lowest + SEMITONES_PER_OCTAVE]


def _invert_down(chord):
    """Invert chord down. Helper for invert_chord()."""
    *core, highest = chord
    return [highest - SEMITONES_PER_OCTAVE] + core


def invert_chord(chord, inversion):
    """Invert chord up or down."""
    chord = list(chord)
    for _ in range(inversion):
        chord = _invert_up(chord)

    for _ in range(-inversion):
        chord = _invert_down(chord)

    return np.array(chord)


def _load_chords():
    """Load chords from CSV file."""
    data = pkgutil.get_data('klang.music', 'data/chords.csv')
    chords = {
        name: np.array(data)
        for name, data
        in parse_music_data_from_csv(data).items()
    }

    return chords


CHORDS = _load_chords()