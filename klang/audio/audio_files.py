"""Writing and reading audio WAV files."""
import wave

import numpy as np
import scipy.io.wavfile

from klang.config import SAMPLING_RATE
from klang.math import normalize_values


__all__ = ['convert_samples_to_float', 'convert_samples_to_int', 'load_wave', 'write_wave']


def convert_samples_to_float(samples):
    """Convert PCM audio samples to float [-1.0, ~1.0]."""
    samples = np.asarray(samples)
    if not np.issubdtype(samples.dtype, np.integer):
        raise ValueError('Already float samples!')

    maxValue = abs(np.iinfo(samples.dtype).min)
    return samples / maxValue


def convert_samples_to_int(samples, dtype=np.int16):
    """Convert float audio samples [-1.0, 1.0] to PCM / int."""
    samples = np.asarray(samples)
    if np.issubdtype(samples.dtype, np.integer):
        raise ValueError('Already int samples!')

    maxValue = np.iinfo(dtype).max
    return (maxValue * samples).astype(dtype)


def load_wave(filepath):
    """Load WAV file."""
    #rate, data = scipy.io.wavfile.read(filepath)  # Can not handle some mono files?!
    with wave.open(filepath, 'rb') as waveRead:
        sampleWidth = waveRead.getsampwidth()
        if not sampleWidth == 2:
            fmt = 'Only 16 bit WAV supported at the moment. Not %s!'
            msg = fmt % sampleWidth
            raise ValueError(msg)

        rate = waveRead.getframerate()
        raw = waveRead.readframes(-1)
        data = np.frombuffer(raw, dtype=np.int16)
        nFrames = waveRead.getnframes()
        nChannels = waveRead.getnchannels()
        data = data.reshape((nFrames, nChannels))

    return rate, convert_samples_to_float(data)


def write_wave(audio, filepath, samplingRate=SAMPLING_RATE, dtype=np.int16):
    """Write mono / stereo audio to WAV file."""
    # TODO: 8 bit -> uint8, 24 bit -> ???, 32 bit -> int32
    audio = np.asarray(audio)

    # Scale to full Wertebereich of target bit depth.
    samples = (normalize_values(audio) * np.iinfo(dtype).max).astype(dtype)
    m, n = samples.shape
    assert m > n
    scipy.io.wavfile.write(filepath, samplingRate, samples)
