"""All things audio.

In this module some helper constants / arrays for working with audio.
"""
import numpy as np

from config import BUFFER_SIZE, SAMPLING_RATE


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""

NYQUIST_FREQUENCY = SAMPLING_RATE // 2
"""int: Nyquist frequency."""

MONO_SILENCE = np.zeros(BUFFER_SIZE)
"""array: Default array for mono silence."""

STEREO_SILENCE = np.zeros((2, BUFFER_SIZE))
"""array: Default array for stereo silence."""

T = DT * np.arange(BUFFER_SIZE)
"""array: Buffer time points."""

T1 = DT * np.arange(BUFFER_SIZE + 1)
"""array: Buffer time points plus one (continuation)."""


# Make all numpy ndarray's in this module read-only
for _arr in [val for val in globals().values() if isinstance(val, np.ndarray)]:
    _arr.setflags(write=False)
