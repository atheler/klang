"""Rhyhtm related stuff.

Micro rhythms as tempo deviations.

omega(phi) = 1. + omega^~(phi)

Euclidian Rhyhtm
----------------

  - https://github.com/WilCrofter/Euclidean_Rhythms/blob/master/euclidean_rhythms.py
  - https://pdfs.semanticscholar.org/c652/d0a32895afc5d50b6527447824c31a553659.pdf
"""
# TODO: type hinting
import fractions

import numpy as np
import scipy.interpolate

from klang.constants import TAU
from klang.music.note_formatting import cumsum
from klang.music.note_values import QUARTER_NOTE
from klang.math import blend
from klang.block import Block


__all__ = ['euclidian_rhythm', 'MicroRhyhtm']


def _compute_bitmap(num_slots, num_pulses):
    """Bjorklund algorithm for Euclidian rhythm.

    Resources:
      - The Theory of Rep-Rate Pattern Generation in the SNS Timing System from
        https://pdfs.semanticscholar.org/c652/d0a32895afc5d50b6527447824c31a553659.pdf
    """
    #print('_compute_bitmap(%d, %d)' % (num_slots, num_pulses))
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

    #print('remainder:', remainder)
    #print('count    :', count)
    #print('level    :', level)

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


def format_notes(notes):
    """Usage:
        >>> print(format_notes([QUARTER_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE]))
        [1/4, 1/8, 1/16]
    """
    if isinstance(notes, fractions.Fraction):
        return str(notes)

    return '[%s]' % ', '.join(map(str, notes))


def harmonize(func, phase, n):
    """Extend micro rhythm to full circle TAU."""
    values = func(n * phase % TAU)
    offset = int(n * phase / TAU) * TAU
    return (values + offset) / n


def phrase(func, phase, phrasing, n):
    """Evaluate micro rhythm phase for some phrasing."""
    straight = phase % TAU
    groove = harmonize(func, phase, n)
    return blend(
        straight,
        groove,
        x=phrasing,
    )


class MicroRhyhtm(Block):

    """N tuplet rhythm pattern.

    http://general-theory-of-rhythm.org/basic-principles/
    """

    def __init__(self, notes, phrasing=1., beatValue=QUARTER_NOTE,
                 kind='linear', name=''):
        super().__init__(nInputs=2, nOutputs=1)
        self.notes = notes
        self.beatValue = beatValue
        self.name = name
        self.phrasing = self.inputs[1]
        self.phrasing.set_value(phrasing)
        self.interpolator = self.create_phase_interpolator(notes, kind)

    @staticmethod
    def create_phase_interpolator(notes, kind):
        """Create micro rhythm phase interpolator from note pattern."""
        nNotes = len(notes)
        duration = sum(notes)
        starts = cumsum(notes)
        angles = (TAU / duration * np.r_[starts, duration]).astype(float)
        return scipy.interpolate.interp1d(
            angles,
            np.linspace(0, TAU, nNotes + 1),
            kind,
        )

    def warp(self, phase, n=None):
        """Distort phase according to micro rhythm pattern.

        Kwargs:
            n (int): Harmonics multiplier. How many times to apply micro rhythm
                on the interval [0, TAU).
            """
        n = n or 1 // self.beatValue
        return phrase(self.interpolator, phase, self.phrasing.value, n)

    def update(self):
        phase = self.input.value
        self.output.set_value(self.warp(phase))

    def __str__(self):
        infos = []
        if self.name:
            infos.append(repr(self.name))

        infos.extend([
            format_notes(self.notes),
            'phrasing: %.1f' % self.phrasing.value,
            'beatValue: %s' % self.beatValue,
        ])
        return '%s(notes: %s)' % (type(self).__name__, ', '.join(infos))
