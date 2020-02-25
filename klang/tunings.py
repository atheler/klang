"""All things related to tuning.

Conversion functions, temperaments."""
import re

import numpy as np

from config import KAMMERTON
from klang.constants import DODE, REF_OCTAVE


CENT_PER_OCTAVE = 1200
"""int: Cents per octave. TODO(atheler): To be moved to klang.constants?"""

OCTAVE = 2.
"""float: Octave frequency ratio. TODO(atheler): To be moved to klang.constants?"""

SCIENTIFIC_PITCH_NOTATION_RE = re.compile(r'([CDEFGAB])([#b]*)([-0123456789]+)')
"""re.pattern: Regex pattern for scientific note name."""

PITCHES = {
    'C': 0,
    'D': 2,
    'E': 4,
    'F': 5,
    'G': 7,
    'A': 9,
    'B': 11,
}
"""dict: Pitch char (str) -> Pitch number."""

PITCHES_2 = np.array([
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
])

ACCIDENTAL_SHIFTS = {
    '': 0,
    '#': 1,
    '##': 2,
    'b': -1,
    'bb': -2,
}
"""dict: Accidental string (str) -> Pitch modifier value (int)."""


def frequency_2_pitch(frequency, kammerton=KAMMERTON):
    """Frequency to MIDI note number (equal temperament)."""
    return 69 + 12 * np.log2(frequency / kammerton)


assert frequency_2_pitch(KAMMERTON) == 69


def pitch_2_frequency(noteNumber, kammerton=KAMMERTON):
    """MIDI note number to frequency (equal temperament)."""
    return (2 ** ((noteNumber - 69) / 12)) * kammerton


assert pitch_2_frequency(69) == KAMMERTON


def ratio_2_cent(ratio):
    """Convert frequency ratio to cent."""
    return CENT_PER_OCTAVE * np.log2(ratio)


assert ratio_2_cent(OCTAVE) == CENT_PER_OCTAVE


def cent_2_ratio(cent):
    """Convert cent to frequency ratio."""
    return 2 ** (cent / CENT_PER_OCTAVE)


assert cent_2_ratio(CENT_PER_OCTAVE) == OCTAVE


def note_name_2_pitch(note, midi=False):
    """Convert note name to pitch number. Uses scientific pitch notation by
    default (one octave difference compared to MIDI).

    Args:
        note (str): Note name.

    Kwargs:
        midi (bool): Use scientific (false) or MIDI format (true).

    Returns:
        int: Pitch number.

    Usage:
        >>> note_name_2_pitch('G##4')
        69

        >>> note_name_2_pitch('A4') == note_name_2_pitch('A5', midi=True)
        True
    """
    note = note.title()
    match = SCIENTIFIC_PITCH_NOTATION_RE.match(note)
    if match is None:
        raise ValueError('Can not parse note %r' % note)

    pitchChar, shiftStr, octaveStr = match.groups()
    pitch = PITCHES[pitchChar]
    shift = ACCIDENTAL_SHIFTS[shiftStr]
    octave = int(octaveStr) + 1 - int(midi)
    return pitch + shift + octave * DODE


assert note_name_2_pitch('c-1') == 0
assert note_name_2_pitch('c#-1') == 1
assert note_name_2_pitch('Cb0') == 11
assert note_name_2_pitch('B0') == 23
assert note_name_2_pitch('a4') == 69
assert note_name_2_pitch('G##4') == 69
assert note_name_2_pitch('A4') == note_name_2_pitch('A5', midi=True)


def pitch_2_note_name(pitch, midi=False):
    """Convert pitch number(s) to note name(s)."""
    """
    octave, note = np.divmod(pitch, DODE)

    # Element wise string concatenation
    return np.core.defchararray.add(
        PITCHES_2[note],
        (octave - 1 + int(midi)).astype(str)
    ).squeeze()
    """
    octave, note = divmod(pitch, DODE)
    noteName = PITCHES_2[note] + str(octave - 1 + int(midi))
    return noteName.upper()


assert note_name_2_pitch(pitch_2_note_name(69)) == 69
assert note_name_2_pitch(pitch_2_note_name(69, midi=True), midi=True) == 69


class Temperament:

    """Tuning temperament."""

    def __init__(self, name, ratios, kammerton=KAMMERTON):
        """Args:
            name (str): Name of the temperament.
            ratios (array): Frequency ratios. At the moment only length-12 are
                supported and first frequency ratio has to be 1.0!
        Kwargs:
            kammerton (frequency): Reference pitch for A4 (or A3 in MIDI).
        """
        assert len(ratios) == DODE and ratios[0] == 1.
        self.name = name
        self.ratios = np.asarray(ratios, dtype=float)
        self.kammerton = kammerton

    def pitch_2_frequency(self, pitch):
        kammertonOffset = -9
        octave, note = np.divmod(pitch + kammertonOffset, DODE)
        return self.kammerton * self.ratios[note] * (2 ** float(octave - REF_OCTAVE))

    def frequency_2_pitch(self, frequency):
        raise NotImplementedError
        # Round to nearest pitch(es)

    def __str__(self):
        return '%s(%r, %.1f Hz)' % (
            self.__class__.__name__,
            self.name,
            self.kammerton,
        )


if __name__ == '__main__':
    kammerton = 442.
    ratios = 2. ** (np.arange(DODE) / DODE)

    EQUAL_TEMPERAMENT = Temperament('Equal', ratios, kammerton=kammerton)
    print(EQUAL_TEMPERAMENT)
    print('Pitch 60 ->', EQUAL_TEMPERAMENT.pitch_2_frequency(60))
    print('Pitch 69 ->', EQUAL_TEMPERAMENT.pitch_2_frequency(69))


    for pitch in range(60, 72):
        print(pitch, '->', pitch_2_note_name(pitch))
