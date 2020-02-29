import collections

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
    """Load music data from CSV.

    Assumed format:
        a,1,2
        b,3,4,5
        c,6,7,8,9

    Args:
        filepath (str): CSV filepath.

    Kwargs:
        sep (str): CSV separator.

    Returns:
        dict: Name (str) -> Data (list).
    """
    dct = {}
    with open(filepath, 'r') as f:
        for line in f.readlines():
            key, *values = line.split(sep)
            dct[key] = [int(v) for v in values]

    return dct


def levenshtein(first, second, deletionCost=1, insertionCost=1, substitutionCost=1):
    """Levenshtein editing distance.

    Args:
        first (str): First string.
        second (str): Second string.

    Kwargs:
        deletionCost ()
    """
    nRows = len(first) + 1
    nCols = len(second) + 1
    assert nRows > 1 and nCols > 1
    H = np.zeros((nRows, nCols), dtype=int)
    H[:, 0] = np.arange(nRows)
    H[0, :] = np.arange(nCols)
    for row, a in enumerate(first, start=1):
        for col, b in enumerate(second, start=1):
            H[row, col] = min(
                H[row-1][col] + deletionCost,                      # Cost of deletions
                H[row][col-1] + insertionCost,                     # Cost of insertions
                H[row-1][col-1] + substitutionCost * int(a != b),  # Cost of substitutions
            )

    return H[row, col]


def _filter_values(dct, value):
    """Get keys for a certain value."""
    return [key for key, val in dct.items() if val == value]


def _listify(sequence):
    """String list representation of sequence.

    Usage:
        >>> _listify([1, 2, 3])
        '1, 2 or 3'
    """
    if len(sequence) > 1:
        ret = ', '.join(map(repr, sequence[:-1]))
        ret += ' or %r' % sequence[-1]
    else:
        ret = ', '.join(map(repr, sequence))

    return ret


def find_item(dct, name):
    """Try to find item in dictionary by name (key has to be a string). In case
    of ambiguity present alternatives (lowest Levenshtein distance).
    """
    if name in dct:
        return dct[name]

    distances = {
        key: levenshtein(name, key, insertionCost=0) for key in dct
    }
    hist = collections.Counter(distances.values())
    minDist = min(hist)
    if minDist > 0.0:
        msg = 'Could not find %r!' % name
        alternatives = _filter_values(distances, value=minDist)
        if alternatives:
            msg += ' Did you mean: %s?' % _listify(alternatives)

        raise ValueError(msg)


    candidates = _filter_values(distances, value=0.0)
    if len(candidates) > 1:
        msg = 'Ambiguous name %r! Did you mean: %s?' % (name, _listify(candidates))
        raise ValueError(msg)

    key, = candidates
    return dct[key]
