"""Musical scales.

A scale is a list of semitone intervals.

Resources:
  - https://ianring.com/musictheory/scales/
"""
import numpy as np
from matplotlib import pyplot as plt

from config import SCALES_FILEPATH
from klang.constants import DODE, TAU
from klang.music.tunings import NOTES
from klang.util import find_item, load_music_data_from_csv


PITCHES = np.arange(DODE)
"""array:"""

MASK = 2 ** PITCHES
"""array: Pitch number values for encoding."""

CIRCLE_OF_FIFTHS = np.array([(7 * i) % 12 for i in range(DODE)])
"""array: Pitches of the circle of fifths."""

_ANGLES = np.linspace(0, TAU, DODE, endpoint=False)
"""array: Chromatic angles."""

ALL_POSSIBLE_SCALES = []
"""list: All possible scales. Ordered by binary code."""

KNOWN_SCALES = {}
"""dict: Scale name (str) -> Scale code (int)."""


def find_scale(name):
    """Find scale by name in database."""
    code = find_item(KNOWN_SCALES, name, augments=[' scale', ' mode'])
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
    """Get binary scale code for scale."""
    pitches = scale_2_pitches(scale)
    return MASK[pitches].sum()


def code_2_scale(code):
    """Build scale from binary scale code."""
    assert 0 <= code <= 2 ** DODE
    pitches = []
    for pitch in PITCHES:
        if code & (1 << pitch):
            pitches.append(pitch)

    return pitches_2_scale(pitches)


def all_possible_scales():
    """All 2048 possible music scales in an octave."""
    return [
        code_2_scale(code) for code in range(2 ** DODE)
    ]


def format_circle_of_fifth_polar_plot(ax):
    """Format a polar subplot so that it fits a circle of fifths plot."""
    north = 'N'
    ax.set_theta_zero_location(north)

    clockwise = -1
    ax.set_theta_direction(clockwise)

    ax.set_xticks(_ANGLES)

    labels = NOTES[CIRCLE_OF_FIFTHS]
    ax.set_xticklabels(labels)

    ax.set_yticks([])

    ax.grid(False)


def plot_scale_in_circle_of_fifth(scale, ax=None):
    """Plot a music scale in a circle of fifth plot."""
    pitches = scale_2_pitches(scale)
    ax = ax or plt.gca()
    xy = np.array([
        _ANGLES[CIRCLE_OF_FIFTHS[pitches]],
        np.ones_like(pitches),
    ]).T
    polygon = plt.Polygon(xy, closed=True)
    ax.add_artist(polygon)

    format_circle_of_fifth_polar_plot(ax)

    return polygon


ALL_POSSIBLE_SCALES = all_possible_scales()


# Load scales from database
KNOWN_SCALES = {
    name: scale_2_code(scale)
    for name, scale
    in load_music_data_from_csv(SCALES_FILEPATH).items()
}


def main():
    """Scales circle of fifths plot demo."""
    import math

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

    def plotting_shape(n):
        """Get a nice subplot layout from number of subplots."""
        nRows = math.floor(n ** .5)
        nCols = math.ceil(n ** .5)
        while nRows * nCols < n:
            nCols += 1

        return nRows, nCols


    shape = plotting_shape(len(scales))

    fig, axarr = plt.subplots(*shape, subplot_kw=dict(projection='polar'))
    for name, scale, ax in zip(names, scales, axarr.ravel()):
        plot_scale_in_circle_of_fifth(scale, ax=ax)
        ax.set_title(name.title(), y=1.2)

    margin = .1
    plt.subplots_adjust(left=margin, right=1. - margin, top=1-margin, bottom=margin, hspace=.9)
    plt.show()


if __name__ == '__main__':
    main()