"""Musical scales.

Resources:
  - https://ianring.com/musictheory/scales/
"""
import collections

import numpy as np
from matplotlib import pyplot as plt

from klang.constants import DODE, TAU
from klang.tunings import NOTES


PITCHES = np.arange(DODE)
""""""

MASK = 2 ** PITCHES
"""array: Pitch number values for encoding."""

QUINTE_SEMITONES = 7
"""int: Number of semitones in a perfect fifth."""

CIRCLE_OF_FIFTHS_PITCHES = (QUINTE_SEMITONES * PITCHES) % DODE
"""array: Pitches of the circle of fifths."""

_ANGLES = np.linspace(0, TAU, DODE, endpoint=False)
"""array: Chromatic angles."""

ALL_POSSIBLE_SCALES = []
"""list: All possible scales. Ordered by binary code."""


KNOWN_SCALES = {
    'major': 2741
}


def get_scale_by_name(name):
    key = name.lower()
    if key not in KNOWN_SCALES:
        fmt = 'Do not recognize scale %r!'
        raise ValueError(fmt % name)

    code = KNOWN_SCALES[key]
    return ALL_POSSIBLE_SCALES[code]


def scale_2_pitches(scale):
    """Get scale pitches."""
    return np.roll(np.cumsum(scale), shift=1) % DODE


def pitches_2_scale(pitches):
    """Convert pitches to intervals scale representation."""
    pitches = np.sort(np.mod(pitches, DODE))
    return np.diff(pitches, append=DODE)


assert np.all(
    pitches_2_scale([0, 2, 4, 5, 7, 9, 11]) == (2, 2, 1, 2, 2, 2, 1)
)


def scale_2_code(scale):
    pitches = scale_2_pitches(scale)
    return MASK[pitches].sum()


def code_2_scale(code):
    assert 0 <= code <= 2 ** DODE
    pitches = []
    for pitch in PITCHES:
        if code & (1 << pitch):
            pitches.append(pitch)

    return pitches_2_scale(pitches)

















SCALES = {
    'aeolian': (2, 1, 2, 2, 1, 2, 2),
    'augmented': (3, 1, 3, 1, 3, 1),
    'augmentedfifth': (2, 2, 1, 2, 1, 1, 2, 1),
    'bluesmajor': (3, 2, 1, 1, 2, 3),
    'bluesminor': (3, 2, 1, 1, 3, 2),
    'chromatic': (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    'diminished': (2, 1, 2, 1, 2, 1, 2, 1),
    'dorian': (2, 1, 2, 2, 2, 1, 2),
    'halfwhole': (1, 2, 1, 2, 1, 2, 1, 2),
    'harmonicminor': (2, 1, 2, 2, 1, 3, 1),
    'ionian': (2, 2, 1, 2, 2, 2, 1),
    'japanese': (1, 4, 2, 1, 4),
    'locrian': (1, 2, 2, 1, 2, 2, 2),
    'lydian': (2, 2, 2, 1, 2, 2, 1),
    'major': (2, 2, 1, 2, 2, 2, 1),
    'melodicminor': (2, 1, 2, 2, 2, 2, 1),
    'minor': (2, 1, 2, 2, 1, 2, 2),
    'mixolydian': (2, 2, 1, 2, 2, 1, 2),
    'oriental': (1, 3, 1, 1, 3, 1, 2),
    'pentatonicmajor': (2, 2, 3, 2, 3),
    'pentatonicminor': (3, 2, 2, 3, 2),
    'phrygian': (1, 2, 2, 2, 1, 2, 2),
    'wholehalf': (2, 1, 2, 1, 2, 1, 2, 1),
    'wholetone': (2, 2, 2, 2, 2, 2),
}
"""dict: Scale name (str) -> Scale intervals (tuple). From the python-musical
project (https://github.com/wybiral/python-musical).
"""






def all_possible_scales():
    """All 2048 possible music scales in an octave."""
    return [
        code_2_scale(code) for code in range(2 ** DODE)
    ]


ALL_POSSIBLE_SCALES = all_possible_scales()



def format_circle_of_fifth_polar_plot(ax):
    """Format a polar subplot so that it fits a circle of fifths plot."""
    north = 'N'
    ax.set_theta_zero_location(north)

    clockwise = -1
    ax.set_theta_direction(clockwise)

    ax.set_xticks(_ANGLES)

    labels = NOTES[CIRCLE_OF_FIFTHS_PITCHES]
    ax.set_xticklabels(labels)

    ax.set_yticks([])

    ax.grid(False)


def plot_scale_in_circle_of_fifth(scale, ax=None):
    """Plot a music scale in a circle of fifth plot."""
    pitches = scale_2_pitches(scale)
    ax = ax or plt.gca()
    xy = np.array([
        _ANGLES[CIRCLE_OF_FIFTHS_PITCHES[pitches]],
        np.ones_like(pitches),
    ]).T
    polygon = plt.Polygon(xy, closed=True)
    ax.add_artist(polygon)

    format_circle_of_fifth_polar_plot(ax)

    return polygon


if __name__ == '__main__':
    import math

    # Scales demo plot. Params:
    scales = SCALES


    def plotting_shape(n):
        """Get a nice subplot layout from number of subplots."""
        nRows = math.floor(n ** .5)
        nCols = math.ceil(n ** .5)
        while nRows * nCols < n:
            nCols += 1

        return nRows, nCols


    shape = plotting_shape(len(SCALES))

    fig, axarr = plt.subplots(*shape, subplot_kw=dict(projection='polar'))
    for (name, scale), ax in zip(SCALES.items(), axarr.ravel()):
        plot_scale_in_circle_of_fifth(scale, ax=ax)
        ax.set_title(name.title(), y=1.2)

    margin = .1
    plt.subplots_adjust(left=margin, right=1. - margin, top=1-margin, bottom=margin, hspace=.9)
    plt.show()
