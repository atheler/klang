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


def cycle_pairs(iterable, circular=True):
    """Cycle over pairs in `iterable` generator.

    Args:
        iterable (iterable): Some iterable.

    Kwargs:
        circular (bool): If true yields (end, start) for the last iteration.

    Yields:
        tuple: Pairs over `iterable`.
    """
    if len(iterable) < 2:
        return

    iterator = iter(iterable)
    first = prev = next(iterator)
    for item in iterator:
        yield prev, item
        prev = item

    if circular:
        yield item, first


def load_music_data_from_csv(filepath, sep=','):
    dct = {}
    with open(filepath, 'r') as f:
        for line in f.readlines():
            key, *values = line.split(sep)
            dct[key] = [int(v) for v in values]

    return dct
