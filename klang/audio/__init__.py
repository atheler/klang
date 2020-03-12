"""All things audio."""
import numpy as np

from config import BUFFER_SIZE, SAMPLING_RATE


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""

NYQUIST_FREQUENCY = SAMPLING_RATE // 2
"""int: Nyquist frequency."""

MONO_SILENCE = np.zeros(BUFFER_SIZE)
MONO_SILENCE.flags.writeable = False
"""array: Default array for mono silence."""

STEREO_SILENCE = np.zeros((2, BUFFER_SIZE))
STEREO_SILENCE.flags.writeable = False
"""array: Default array for stereo silence."""

T = DT * np.arange(BUFFER_SIZE)
T.flags.writeable = False
"""array: Buffer time points."""

T1 = DT * np.arange(BUFFER_SIZE + 1)
T1.flags.writeable = False
"""array: Buffer time points plus one (continuation)."""
