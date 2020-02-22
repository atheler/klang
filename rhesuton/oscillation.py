"""Note:
  - scipy.signal waveform functions are quite slow.
"""
import numpy as np

from rhesuton.math import wrap
from rhesuton.constants import TAU
from config import SAMPLING_RATE


DT = 1. / SAMPLING_RATE


def square_waveform(phase):
    """Sqaure wave function."""
    return 2. * (wrap(phase) >= 0).astype(float) - 1.


def sawtooth_waveform(phase):
    """Sawtooth wave function."""
    return 2. * np.mod(phase, TAU) / TAU - 1.


def triangle_waveform(phase):
    """Triangle wave function."""
    return 1. - np.abs((4 * wrap(phase) / TAU) % 4 - 2)


WAVE_FUNCTIONS = {
    'sine': np.sin,
    'square': square_waveform,
    'sawtooth': sawtooth_waveform,
    'triangle': triangle_waveform,
}


def sample_wave(nSamples, frequency, startPhase=0., wave_func=np.sin):
    """Sample wave function."""
    t = DT * np.arange(nSamples + 1)
    phase = TAU * frequency * t + startPhase
    signal = wave_func(phase[..., :-1])
    return signal, phase[..., -1]