#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issues:
  - REF_OCTAVE = 5. Is this compatible to what piano tuners refer to reference
    octave? Should it be set to 4?

Resources:
  - https://en.wikipedia.org/wiki/MIDI_tuning_standard
  - https://en.wikipedia.org/wiki/Equal_temperament
  - https://www.math.uwaterloo.ca/~mrubinst/tuning/tuning.html

Author: atheler
"""
import collections

import numpy as np
import matplotlib.pyplot as plt

from config import SAMPLING_RATE
from rhesuton.constants import TAU
from rhesuton.math import normalize_values
from rhesuton.midi import pitch_2_frequency
from rhesuton.temperaments import EQUAL_TEMPERAMENT, YOUNG_TEMPERAMENT
from rhesuton.util import write_wave

"""dict: Bit depth (int) -> numpy dtype."""

"""array: """


Note = collections.namedtuple('Note', 'pitch amplitude duration')


def render_pattern(pattern, temperament, samplingRate=SAMPLING_RATE,
                   normalize=True):
    """Note pattern -> mono sound buffer."""
    # Find overall duration / init buffer
    end = max(start + note.duration for start, note in pattern)
    length = int(end * samplingRate)
    buf = np.zeros(length, dtype=float)

    for start, note in pattern:
        startIdx = int(start * samplingRate)
        endIdx = int((start + note.duration) * samplingRate)
        frequency = temperament(note.pitch)
        t = 1. / samplingRate * np.arange(endIdx - startIdx)
        oscillation = np.sin(TAU * frequency * t)
        buf[startIdx:endIdx] += note.amplitude * oscillation

    if normalize:
        buf = normalize_values(buf)

    return buf


if __name__ == '__main__':
    pattern = [
        (0., Note(60, 1., .5)),
        (1., Note(65, 1., .5)),
        (2., Note(67, 1., .5)),

        (4., Note(60, 1., 4.)),
        (4., Note(65, 1., 4.)),
        (4., Note(67, 1., 4.)),
    ]




    for temperament in [EQUAL_TEMPERAMENT, YOUNG_TEMPERAMENT]:
        buf = render_pattern(pattern, temperament)
        filepath = '%s.wav' % temperament.name
        write_wave(buf, filepath)
        print('Wrote buffer to %r' % filepath)

    plt.plot(buf)
    plt.show()
