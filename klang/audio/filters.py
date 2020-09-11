"""Ring buffer based filters."""
from typing import Sequence
import warnings

import numpy as np

from klang.config import SAMPLING_RATE, BUFFER_SIZE
from klang.ring_buffer import RingBuffer


__all__ = ['ForwardCombFilter', 'BackwardCombFilter', 'EchoFilter']

DEFAULT_ALPHA: float = .9
"""Default gain value for ring buffer filters."""

USE_PYTHON_FALLBACK: bool = True
"""Use Python fallback for ring buffer filters instead of C-extensions."""

try:
    from klang.audio._filters import ForwardCombFilter as CForwardCombFilter
    from klang.audio._filters import BackwardCombFilter as CBackwardCombFilter
    from klang.audio._filters import EchoFilter as CEchoFilter
    USE_PYTHON_FALLBACK = False

except ImportError:
    warnings.warn((
        'Python fallback for ring buffer based filters. Delay times should be '
        f'at least >= BUFFER_SIZE samples (currently {BUFFER_SIZE}). At a '
        f'sampling rate of {SAMPLING_RATE} Hz this corresponds to '
        f'at least {1000 * BUFFER_SIZE / SAMPLING_RATE:.3f} ms.'
    ))


class PyRingBufferFilter:

    """Base class of Python ring buffer filters."""

    def __init__(self, k: int, alpha: float = DEFAULT_ALPHA):
        """Args:
            k: Ring buffer length.

        Kwargs:
            alpha: Gain factor.
        """
        self.alpha = alpha
        self.ring = RingBuffer(k)

    def filter(self, x: Sequence) -> np.ndarray:
        """Process input samples x."""
        raise NotImplementedError


class PyForwardCombFilter(PyRingBufferFilter):

    """Feed forward comb filter.

    See https://en.wikipedia.org/wiki/Comb_filter.
    """

    def filter(self, x):
        y = x + self.alpha * self.ring.peek(len(x))
        self.ring.extend(x)
        return y


class PyBackwardCombFilter(PyRingBufferFilter):

    """Feed backward comb filter.

    See https://en.wikipedia.org/wiki/Comb_filter.
    """

    def filter(self, x):
        y = x + self.alpha * self.ring.peek(len(x))
        self.ring.extend(y)
        return y


class PyEchoFilter(PyRingBufferFilter):

    """Feedback delay."""

    def filter(self, x):
        y = self.ring.peek(len(x)).copy()
        self.ring.extend(x + self.alpha * y)
        return y


ForwardCombFilter: type = type
"""Monkey patch class placeholder."""

BackwardCombFilter: type = type
"""Monkey patch class placeholder."""

EchoFilter: type = type
"""Monkey patch class placeholder."""


# Monkey patch appropriate filter types
if USE_PYTHON_FALLBACK:
    ForwardCombFilter = PyForwardCombFilter
    BackwardCombFilter = PyBackwardCombFilter
    EchoFilter = PyEchoFilter

else:
    ForwardCombFilter = CForwardCombFilter
    BackwardCombFilter = CBackwardCombFilter
    EchoFilter = CEchoFilter
