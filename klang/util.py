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


def find_alternative_names(dct, name):
    """Find alternative key names in dict.

    Usage:
        >>> dct = {'lorem ipsum': 0, 'lorem dolor': 1, 'sit amet': 2}
        ... find_alternative_names(dct, 'lorem')
         {'lorem dolor', 'lorem ipsum'}
    """
    altNames = set()
    for word in name.split():
        for key in dct:
            if word in key or key in word:
                altNames.add(key)

    return altNames


def find_item(dct, name, augments=None):
    """Find item in dictionary by name. Also try augmented versions of original
    names. If item can not be located propose alternatives.
    """
    # Prepare name augments
    augments = augments or []
    if '' not in augments:
        augments = [''] + augments

    # Try to find item
    candidates = []
    for aug in augments:
        key = name + aug
        if key in dct:
            candidates.append(key)

    nCandidates = len(candidates)
    if nCandidates == 0:
        msg = 'Could not find item %r!' % name

        # Propose alternatives
        alternatives = find_alternative_names(dct, name)
        if alternatives:
            aStr = ', '.join(map(repr, alternatives))
            msg += (' Did you mean: %s?' % aStr)

        raise ValueError(msg)

    if nCandidates > 1:
        msg = 'Found to many candidates! %s'
        raise ValueError(msg % ' ,'.join(
            candidates
        ))

    key = candidates[0]
    return dct[key]
