"""Music chords."""
import numpy as np

from klang.constants import SEMITONES_PER_OCTAVE
#from klang.scraping import chords


CHORDS = {
    '"ode-to-napoleon" hexachord': np.array([0, 1, 4, 5, 8, 9]),
    'augmented': np.array([0, 4, 8]),
    'augmented eleventh': np.array([ 0,  4,  7, 10, 14, 30]),
    'augmented major seventh': np.array([ 0,  4,  8, 11]),
    'augmented seventh': np.array([ 0,  4,  8, 10]),
    'diminished': np.array([0, 3, 6]),
    'diminished major seventh': np.array([ 0,  3,  6, 11]),
    'diminished seventh (leading-tone and secondary)': np.array([0, 3, 6, 9]),
    'dominant': np.array([0, 4, 7]),
    'dominant eleventh': np.array([ 0,  4,  7, 10, 14, 29]),
    'dominant minor ninth': np.array([ 0,  4,  7, 10, 13]),
    'dominant ninth': np.array([ 0,  4,  7, 10, 14]),
    'dominant parallel': np.array([0, 3, 7]),
    'dominant seventh': np.array([ 0,  4,  7, 10]),
    'dominant seventh flat five': np.array([ 0,  4,  6, 10]),
    'dominant seventh sharp nine / hendrix': np.array([ 0,  4,  7, 10, 15]),
    'dominant thirteenth': np.array([ 0,  4,  7, 10, 14, 29, 33]),
    'dream': np.array([0, 5, 6, 7]),
    'elektra': np.array([ 0,  7,  9, 13, 28]),
    'farben': np.array([ 0,  8, 11, 16, 33]),
    'half-diminished seventh': np.array([ 0,  3,  6, 10]),
    'harmonic seventh': np.array([ 0,  4,  7, 10]),
    'leading-tone triad': np.array([0, 3, 6]),
    'lydian': np.array([ 0,  4,  7, 11, 18]),
    'magic': np.array([ 0,  1,  5,  6, 10, 12, 27, 29]),
    'major': np.array([0, 4, 7]),
    'major eleventh': np.array([ 0,  4,  7, 11, 14, 29]),
    'major ninth': np.array([ 0,  4,  7, 11, 14]),
    'major seventh': np.array([ 0,  4,  7, 11]),
    'major seventh sharp eleventh': np.array([ 0,  4,  8, 11, 18]),
    'major sixth': np.array([0, 4, 7, 9]),
    'major sixth ninth ("6 add 9", nine six, 6/9)': np.array([ 0,  4,  7,  9, 14]),
    'major thirteenth': np.array([ 0,  4,  7, 11, 14, 30, 33]),
    'mediant': np.array([0, 3, 7]),
    'minor': np.array([0, 3, 7]),
    'minor eleventh': np.array([ 0,  3,  7, 10, 14, 29]),
    'minor major seventh': np.array([ 0,  3,  7, 11]),
    'minor ninth': np.array([ 0,  3,  7, 10, 14]),
    'minor seventh': np.array([ 0,  3,  7, 10]),
    'minor sixth': np.array([0, 3, 7, 9]),
    'minor sixth ninth (6/9)': np.array([ 0,  3,  7,  9, 14]),
    'minor thirteenth': np.array([ 0,  3,  7, 10, 14, 29, 33]),
    'mu': np.array([0, 2, 4, 7]),
    'mystic': np.array([ 0,  6, 10, 16, 33, 38]),
    'neapolitan': np.array([1, 5, 8]),
    'ninth augmented fifth': np.array([ 0,  4,  8, 10, 14]),
    'ninth flat fifth': np.array([ 0,  4,  6, 10, 14]),
    'northern lights': np.array([ 1,  2,  8, 12, 27, 30, 31, 34, 35, 40, 55]),
    'petrushka': np.array([ 0,  1,  4,  6,  7, 10]),
    'power chord': np.array([0, 7]),
    'psalms': np.array([0, 3, 7]),
    'secondary dominant': np.array([0, 4, 7]),
    'secondary leading-tone': np.array([0, 3, 6]),
    'secondary supertonic': np.array([0, 3, 7]),
    'seven six': np.array([ 0,  4,  7,  9, 10]),
    'seventh suspension four': np.array([ 0,  5,  7, 10]),
    'so what': np.array([ 0,  5, 10, 15, 31]),
    'subdominant': np.array([0, 4, 7]),
    'subdominant parallel': np.array([0, 3, 7]),
    'submediant': np.array([0, 3, 7]),
    'subtonic': np.array([0, 4, 7]),
    'supertonic': np.array([0, 3, 7]),
    'suspended': np.array([0, 5, 7]),
    'tonic': np.array([0, 4, 7]),
    'tonic counter parallel': np.array([0, 3, 7]),
    'tonic parallel': np.array([0, 3, 7]),
    'tristan': np.array([ 0,  3,  6, 10]),
    'viennese trichord': np.array([0, 1, 6]),
    'viennese trichord-1': np.array([0, 6, 7]),
}
"""dict: Chord name (str) -> Chord mapping (array).
Source: https://en.wikipedia.org/wiki/List_of_chords.
"""


def pitch_classes_2_chord(pitchClasses):
    """Parse pitch classes.

    Usage:
        >>> pitch_classes_2_chord('0 4 7 t')
        np.array([0, 4, 7, 10])
    """
    pitchClasses = pitchClasses.replace('t', '10')
    pitchClasses = pitchClasses.replace('A', '10')
    pitchClasses = pitchClasses.replace('e', '11')
    pitchClasses = pitchClasses.replace('B', '11')

    base = 0
    prev = -float('inf')
    chord = []
    for pc in pitchClasses.split(' '):
        pitch = base + int(pc)
        if pitch < prev:
            base += SEMITONES_PER_OCTAVE

        chord.append(base + pitch)
        prev = pitch

    return np.array(chord)


def _invert_up(chord):
    lowest, *core = chord
    return core + [lowest + SEMITONES_PER_OCTAVE]


def _invert_down(chord):
    *core, highest = chord
    return [highest - SEMITONES_PER_OCTAVE] + core


def invert_chord(chord, inversion):
    """Invert chord up or down."""
    chord = list(chord)
    for _ in range(inversion):
        chord = _invert_up(chord)

    for _ in range(-inversion):
        chord = _invert_down(chord)

    return np.array(chord)


MAJOR = [0, 4, 7]
np.testing.assert_equal(invert_chord(MAJOR, inversion=1), [4, 7, 12])
np.testing.assert_equal(invert_chord(MAJOR, inversion=2), [7, 12, 16])
np.testing.assert_equal(invert_chord(MAJOR, inversion=-1), [-5, 0, 4])
np.testing.assert_equal(invert_chord(MAJOR, inversion=-2), [-8, -5, 0])
