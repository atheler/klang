import numpy as np

from oscillation import DT


def sample_linear_envelope(nSamples, slope, start=0.):
    """Sample linear envelope."""
    if slope == np.inf:
        return np.ones(nSamples), 1.

    if slope == -np.inf:
        return np.zeros(nSamples), 0.

    t = DT * np.arange(nSamples + 1)
    signal = (slope * t + start).clip(min=0., max=1.)
    return signal[:-1], signal[-1]


def calculate_slope(duration):
    """Linear slope for given duration."""
    if duration == 0:
        return np.inf

    return 1. / duration