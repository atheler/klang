import numpy as np
from scipy.io import wavfile

from config import SAMPLING_RATE, BIT_DEPTH

_WAVE_DTYPES = {
    #8: np.uint8,
    16: np.int16,
    #24: ???
    #32: np.int32,
}


def write_wave(audio, filepath, samplingRate=SAMPLING_RATE, bitDepth=BIT_DEPTH):
    """Write mono / stereo audio to WAV file."""
    # TODO: 8 bit -> uint8, 24 bit -> ???, 32 bit -> int32
    assert bitDepth in _WAVE_DTYPES
    dtype = _WAVE_DTYPES[bitDepth]
    audio = np.asarray(audio)

    # Scale to full Wertebereich of target bit depth.
    maxVal = np.abs(audio).max()
    audio = audio / maxVal
    samples = (audio * np.iinfo(dtype).max).astype(dtype)

    wavfile.write(filepath, samplingRate, samples)