"""All things audio.

In this module some helper constants / arrays for working with audio.
"""
import functools

import numpy as np

from config import BUFFER_SIZE, SAMPLING_RATE


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""

NYQUIST_FREQUENCY = SAMPLING_RATE // 2
"""int: Nyquist frequency."""


def _read_only(func):
    """Make returned numpy array from func read-only."""
    @functools.wraps(func)
    def decorated_func(*args, **kwargs):
        arr = func(*args, **kwargs)
        arr.setflags(write=False)
        return arr

    return decorated_func


@functools.lru_cache()
@_read_only
def get_silence(shape):
    """Get some silence. All zero array. Cached."""
    return np.zeros(shape)


@functools.lru_cache()
@_read_only
def get_time(length, dt=DT):
    """Get time values. Cached."""
    return dt * np.arange(length)


MONO_SILENCE = get_silence(BUFFER_SIZE)
"""array: Default array for mono silence."""

STEREO_SILENCE = get_silence((2, BUFFER_SIZE))
"""array: Default array for stereo silence."""

T = get_time(BUFFER_SIZE, DT)
"""array: Buffer time points."""

T1 = get_time(BUFFER_SIZE + 1, DT)
"""array: Buffer time points plus one (continuation)."""

ONES = np.ones(BUFFER_SIZE)
"""array: Nothing but ones."""


# Make all numpy ndarray's in this module read-only.
# TODO(atheler): Deprecated. To be deleted.
for _arr in [val for val in globals().values() if isinstance(val, np.ndarray)]:
    _arr.setflags(write=False)
