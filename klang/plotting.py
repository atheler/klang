"""Some plotting functions."""
import fractions
import math

import numpy as np

from klang.constants import TAU
from klang.music.pitch import PITCH_NAMES, CIRCLE_OF_FIFTHS
from klang.music.scales import _ANGLES, scale_2_pitches


def fraction_ticks(ticks, base, symbol, maxDenominator=10):
    """Form ticks as fractions."""
    fracs = [
        fractions.Fraction(tick / base).limit_denominator(maxDenominator)
        for tick in ticks
    ]

    def labeler(frac):
        if frac.numerator == 0:
            return r'$0$'

        if frac.numerator == 1:
            if frac.denominator == 1:
                return r'$%s$' % symbol

            return r'$\frac{%s}{%d}$' % (symbol, frac.denominator)

        return r'$\frac{%d}{%d}%s$' % (frac.numerator, frac.denominator, symbol)

    return [labeler(frac) for frac in fracs]


def set_radian_xticks(ax):
    ticks = ax.get_xticks()
    labels = fraction_ticks(ticks, TAU, r'\tau')
    ax.set_xticklabels(labels)


def plot_metre(ax, metre):
    """Plot metre lines over axis."""
    import matplotlib.pyplot as plt

    cm = plt.get_cmap()
    for phi in np.linspace(0, TAU, metre.numerator, endpoint=False):
        ax.axvline(phi, ls=':', c=cm(phi / TAU))


def nice_plotting_shape(n):
    """Get a nice subplot layout from number of subplots."""
    nRows = math.floor(n ** .5)
    nCols = math.ceil(n ** .5)
    while nRows * nCols < n:
        nCols += 1

    return nRows, nCols


def format_circle_of_fifth_polar_plot(ax):
    """Format a polar subplot so that it fits a circle of fifths plot."""
    north = 'N'
    ax.set_theta_zero_location(north)

    clockwise = -1
    ax.set_theta_direction(clockwise)

    ax.set_xticks(_ANGLES)

    pitchNames = np.array(PITCH_NAMES)
    labels = pitchNames[CIRCLE_OF_FIFTHS]
    ax.set_xticklabels(labels)

    ax.set_yticks([])

    ax.grid(False)


def plot_scale_in_circle_of_fifth(scale, ax=None):
    """Plot a music scale in a circle of fifth plot."""
    import matplotlib.pyplot as plt

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
