"""Array helper functions and constants."""
import functools

import numpy as np

from klang.config import SAMPLING_RATE, BUFFER_SIZE


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""

INTERVAL = DT * BUFFER_SIZE
"""float: Buffer duration"""

NYQUIST_FREQUENCY = SAMPLING_RATE // 2
"""int: Nyquist frequency."""


@functools.lru_cache()
def get_silence(shape, dtype=float):
    """Get some silence. All zero array. Cached."""
    arr = np.zeros(shape, dtype)
    arr.setflags(write=False)
    return arr


@functools.lru_cache()
def get_time(length, dt=DT):
    """Get time values. Cached."""
    arr = dt * np.arange(length)
    arr.setflags(write=False)
    return arr


MONO_SILENCE = get_silence(BUFFER_SIZE)
"""array: Default array for mono silence."""

STEREO_SILENCE = get_silence((2, BUFFER_SIZE))
"""array: Default array for stereo silence."""

T = get_time(BUFFER_SIZE, DT)
"""array: Buffer time points."""


# Make all numpy ndarray's in this module read-only.
# TODO(atheler): Deprecated. To be deleted.
for _arr in [val for val in globals().values() if isinstance(val, np.ndarray)]:
    _arr.setflags(write=False)