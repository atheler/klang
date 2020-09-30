"""Music pitches and notes."""
import re

import numpy as np

from klang.constants import DODE


__all__ = [
    'PITCH_CLASSES', 'PITCH_NAMES', 'CIRCLE_OF_FIFTHS', 'note_name_2_pitch',
    'pitch_2_note_name',
]

PITCH_CLASSES = np.arange(DODE)
"""array: All base pitches."""

PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
"""list: Pitch / note names."""

CIRCLE_OF_FIFTHS = (7 * PITCH_CLASSES) % DODE
"""array: Pitches of the circle of fifths."""

SCIENTIFIC_PITCH_NOTATION_RE = re.compile(r'([CDEFGAB])([#b]{0,2})([-0123456789]+)')
"""re.pattern: Regex pattern for scientific note name."""

ACCIDENTAL_SHIFTS = {
    '': 0,
    '#': 1,
    '##': 2,
    'b': -1,
    'bb': -2,
}
"""dict: Accidental string (str) -> Pitch modifier value (int)."""


def note_name_2_pitch(noteName: str) -> int:
    """Convert note name to pitch number (scientific pitch notation).

    Args:
        noteName: Scietific pitch notation.

    Returns:
        Pitch number.

    Usage:
        >>> note_name_2_pitch('G##4')
        69
    """
    match = SCIENTIFIC_PITCH_NOTATION_RE.match(noteName.title())
    if not match:
        raise ValueError('Can not parse note %r' % noteName)

    pitchChar, shiftStr, octaveStr = match.groups()
    pitch = PITCH_NAMES.index(pitchChar)
    shift = ACCIDENTAL_SHIFTS[shiftStr]
    octave = int(octaveStr) + 1
    return pitch + shift + octave * DODE


def pitch_2_note_name(pitch: int) -> str:
    """Convert pitch number(s) to note name(s)."""
    # TODO: Support for numpy arrays? Do we need this? Via chords?
    """
    octave, note = np.divmod(pitch, DODE)

    # Element wise string concatenation
    return np.core.defchararray.add(
        PITCHES_2[note],
        (octave - 1 + int(midi)).astype(str)
    ).squeeze()
    """
    octave, note = divmod(pitch, DODE)
    noteName = PITCH_NAMES[note] + str(octave - 1)
    return noteName.upper()
