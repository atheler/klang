"""Audio wave functions.

Note:
  - scipy.signal waveform functions are quite slow.
"""
import warnings

import numpy as np

from klang.audio.helpers import DT, get_time
from klang.config import BUFFER_SIZE
from klang.constants import TAU
from klang.math import wrap


__all__ = [
    'WAVE_FUNCTIONS', 'sine', 'square', 'sawtooth', 'triangle', 'random',
    'sample_wave',
]


def sine(phase):
    """Sine wave function."""
    return np.sin(phase)


def square(phase):
    """Square wave function."""
    return 2. * (wrap(phase) >= 0) - 1.


def sawtooth(phase):
    """Sawtooth wave function."""
    return 2. * np.mod(phase, TAU) / TAU - 1.


def triangle(phase):
    """Triangle wave function."""
    return 1. - np.abs((4 * wrap(phase) / TAU) % 4 - 2)


def random(phase):
    """Uniform random wave function."""
    return 2. * np.random.random(size=phase.shape) - 1.


WAVE_FUNCTIONS = {
    'sine': sine,
    'square': square,
    'sawtooth': sawtooth,
    'triangle': triangle,
    'random': random,
}


def sample_wave(frequency, startPhase=0., wave_func=sine, shape=BUFFER_SIZE):
    """Sample wave function."""
    warnings.warn('sample_wave() function to be deprecated?')
    t = get_time(shape)
    phase = TAU * frequency * t + startPhase
    return wave_func(phase), wrap(phase[-1] + TAU * frequency * DT)
