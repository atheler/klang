"""Music pitches and notes."""
import re

import numpy as np

from klang.config import KAMMERTON
from klang.constants import DODE


PITCH_CLASSES = np.arange(DODE)
"""array: All base pitches."""

PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
"""list: Pitch / note names."""

CIRCLE_OF_FIFTHS = (7 * PITCH_CLASSES) % DODE
"""array: Pitches of the circle of fifths."""

SCIENTIFIC_PITCH_NOTATION_RE = re.compile(r'([CDEFGAB])([#b]*)([-0123456789]+)')
"""re.pattern: Regex pattern for scientific note name."""

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
    # TODO(atheler): To be deprecated?
    return 69 + 12 * np.log2(frequency / kammerton)


def pitch_2_frequency(noteNumber, kammerton=KAMMERTON):
    """MIDI note number to frequency (equal temperament)."""
    # TODO(atheler): To be deprecated?
    return (2 ** ((noteNumber - 69) / 12)) * kammerton


assert frequency_2_pitch(KAMMERTON) == 69
assert pitch_2_frequency(69) == KAMMERTON


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
    pitch = PITCH_NAMES.index(pitchChar)
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
    noteName = PITCH_NAMES[note] + str(octave - 1 + int(midi))
    return noteName.upper()


assert note_name_2_pitch(pitch_2_note_name(69)) == 69
assert note_name_2_pitch(pitch_2_note_name(69, midi=True), midi=True) == 69
