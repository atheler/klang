"""Rhyhtm related stuff.


Micro rhythms as tempo deviations.

omega(phi) = 1. + omega^~(phi)

Euclidian Rhyhtm
----------------

  - https://github.com/WilCrofter/Euclidean_Rhythms/blob/master/euclidean_rhythms.py
  - https://pdfs.semanticscholar.org/c652/d0a32895afc5d50b6527447824c31a553659.pdf
"""
import numpy as np

from klang.constants import TAU
from klang.music.metre import FOUR_FOUR


def swing(ratio, metre=FOUR_FOUR):
    """Create swing function. For now only swing ratios between [.5, 2] supported.

    TODO:
      - Different velocity deviation function for more swing?

    Swing function derivation:
        t is in radian (\phi already taken...)

        Basic swing curve:
            \omega(t) = 1 + a\sin(n t)
            \phi(t) = \int_{0}^{t} \omega(k) \mathrm{d}k = t + \frac{a-a\cos(nt))}{n}

        Amplitude a can be computed from the ratio r in the following way:
            t_{r} = \frac{r \tau}{1 + r}

        Then solve for a
            \phi(t_{r})
    """
    # Determine swing amplitude
    firstOffBeat = TAU * ratio / (1. + ratio)
    amp = (TAU / 2 - firstOffBeat) / (1. - np.cos(firstOffBeat))
    assert abs(amp) < 1., 'To much swing!'

    n = metre.denominator
    return lambda phi: phi + amp * (1. - np.cos(n * phi)) / n


def _compute_bitmap(num_slots, num_pulses):
    """Bjorklund algorithm for Euclidian rhythm.

    Resources:
      - The Theory of Rep-Rate Pattern Generation in the SNS Timing System from
        https://pdfs.semanticscholar.org/c652/d0a32895afc5d50b6527447824c31a553659.pdf
    """
    print('_compute_bitmap(%d, %d)' % (num_slots, num_pulses))
    # First, compute the count and remainder arrays
    divisor = num_slots - num_pulses
    remainder = [num_pulses]
    count = []
    level = 0
    cycleLength = 1
    remLength = 1

    while remainder[level] > 1:
        count.append(divisor // remainder[level])
        remainder.append(divisor % remainder[level])
        divisor = remainder[level]
        newLength = (cycleLength * count[level]) + remLength
        remLength = cycleLength
        cycleLength = newLength
        level += 1

    count.append(divisor)

    if remainder[level] > 0:
        cycleLength = (cycleLength * count[level]) + remLength

    print('remainder:', remainder)
    print('count    :', count)
    print('level    :', level)

    def build_string(level, bitmap=None):
        if bitmap is None:
            bitmap = []

        if level == -1:
            bitmap.append(0)
        elif level == -2:
            bitmap.append(1)
        else:
            for i in range(count[level]):
                build_string(level - 1, bitmap)

            if remainder[level]:
                build_string(level - 2, bitmap)

        return bitmap

    return build_string(level)


def euclidian_rhythm(nPulses, nSlots):
    """Euclidian rhyhtm pattern generator."""
    bitmap = _compute_bitmap(nSlots, nPulses)
    return list(reversed(bitmap))
