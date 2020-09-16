"""Musical scales.

A scale is a list of semitone intervals. E.g. (2, 2, 1, 2, 2, 2, 1) for a major
scale. A scale can be converted to pitches with cumsum. [0, 2, 4, 5, 7, 9, 11].

Resources:
  - https://ianring.com/musictheory/scales/
"""
from typing import Sequence, List, Dict
import pkgutil

import numpy as np

from klang.constants import DODE, TAU
from klang.music.pitch import PITCH_CLASSES
from klang.util import find_item, parse_music_data_from_csv


__all__ = [
    'ALL_POSSIBLE_SCALES', 'KNOWN_SCALES', 'find_scale', 'scale_2_pitches',
    'pitches_2_scale',
]


MASK = 2 ** PITCH_CLASSES
"""array: Pitch number values for encoding."""

ALL_POSSIBLE_SCALES: List[np.ndarray] = []
"""All possible scales. Ordered by binary code."""

KNOWN_SCALES: Dict[str, int] = {}
"""Scale name to scale code."""

_ANGLES = np.linspace(0, TAU, DODE, endpoint=False)
"""array: Chromatic angles."""


def find_scale(name: str) -> np.ndarray:
    """Find scale by name in database."""
    code = find_item(KNOWN_SCALES, name)
    return ALL_POSSIBLE_SCALES[code]


def scale_2_pitches(scale: Sequence[int]) -> np.ndarray:
    """Get scale pitches."""
    return np.roll(np.cumsum(scale), shift=1) % DODE


def pitches_2_scale(pitches: Sequence[int]) -> np.ndarray:
    """Convert pitches to intervals scale representation."""
    pitches = np.sort(np.mod(pitches, DODE))
    return np.diff(pitches, append=DODE)


assert np.all(
    pitches_2_scale([0, 2, 4, 5, 7, 9, 11]) == (2, 2, 1, 2, 2, 2, 1)
)


def scale_2_code(scale: Sequence[int]) -> int:
    """Get binary scale code for scale."""
    pitches = scale_2_pitches(scale)
    return MASK[pitches].sum()


def code_2_scale(code: int) -> np.ndarray:
    """Build scale from binary scale code."""
    assert 0 <= code <= 2 ** DODE
    pitches = []
    for pitch in PITCH_CLASSES:
        if code & (1 << pitch):
            pitches.append(pitch)

    return pitches_2_scale(pitches)


def all_possible_scales() -> List[np.ndarray]:
    """All 2048 possible music scales in an octave."""
    return [
        code_2_scale(code) for code in range(2 ** DODE)
    ]


def _load_known_scales() -> Dict[str, np.ndarray]:
    data = pkgutil.get_data('klang.music', 'data/scales.csv')
    scales = {
        name: scale_2_code(scale)
        for name, scale
        in parse_music_data_from_csv(data).items()
    }

    return scales


# Load scales from database
ALL_POSSIBLE_SCALES = all_possible_scales()
KNOWN_SCALES = _load_known_scales()


def main():
    """Scales circle of fifths plot demo."""
    from matplotlib import pyplot as plt

    from klang.plotting import nice_plotting_shape, plot_scale_in_circle_of_fifth

    # Scales demo plot. Params:
    names = [
        'major',
        'minor',
        'adonai malakh mode',
        'aeolian mode',
        'dorian mode',
        'flamenco mode',
        'ionian mode',
        'locrian mode',
        'lydian mode',
        'mixolydian mode',
        'phrygian mode',
        #'blues',
        #'minor pentatonic scale',
        'chromatic',
    ]
    names = list(KNOWN_SCALES)

    scales = [find_scale(n) for n in names]

    shape = nice_plotting_shape(len(scales))

    fig, axarr = plt.subplots(*shape, subplot_kw=dict(projection='polar'))
    for name, scale, ax in zip(names, scales, axarr.ravel()):
        plot_scale_in_circle_of_fifth(scale, ax=ax)
        ax.set_title(name.title(), y=1.2)

    margin = .1
    plt.subplots_adjust(left=margin, right=1. - margin, top=1-margin, bottom=margin, hspace=.9)
    plt.show()


if __name__ == '__main__':
    main()
