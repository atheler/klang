"""Audio wave functions.

Note:
  - scipy.signal waveform functions are quite slow.
"""
import numpy as np

from klang.audio import DT, T
from klang.constants import TAU
from klang.math import wrap


def sine(phase):
    """Sine wave function."""
    return np.sin(phase)


def square(phase):
    """Sqaure wave function."""
    return 2. * (wrap(phase) >= 0).astype(float) - 1.


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


def sample_wave(nSamples, frequency, startPhase=0., wave_func=np.sin):
    """Sample wave function."""
    phase = TAU * frequency * T + startPhase
    return wave_func(phase), wrap(phase[-1] + TAU * frequency * DT)
