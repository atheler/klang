"""Musical note values.

TODO:
  - Note formatting -> in its own module (?).
"""
import collections
import fractions

from klang.music.metre import (
    FOUR_FOUR_METRE, THREE_FOUR_METRE, TWO_FOUR_METRE, SIX_EIGHT_METRE,
    is_complex
)


"""Note value definitions."""


LARGE_NOTE = fractions.Fraction(8, 1)
LONG_NOTE = fractions.Fraction(4, 1)
DOUBLE_WHOLE_NOTE = fractions.Fraction(2, 1)
WHOLE_NOTE = fractions.Fraction(1, 1)
HALF_NOTE = fractions.Fraction(1, 2)
QUARTER_NOTE = fractions.Fraction(1, 4)
EIGHT_NOTE = fractions.Fraction(1, 8)
SIXTEENTH_NOTE = fractions.Fraction(1, 16)
THIRTY_SECOND_NOTE = fractions.Fraction(1, 32)
SIXTY_FOURTH_NOTE = fractions.Fraction(1, 64)
HUNDRED_TWENTY_NOTE = fractions.Fraction(1, 128)
TWO_HUNDRED_FIFTY_SIXTH_NOTE = fractions.Fraction(1, 256)

DOTTED_LARGE_NOTE = fractions.Fraction(12, 1)
DOTTED_LONG_NOTE = fractions.Fraction(6, 1)
DOTTED_DOUBLE_WHOLE_NOTE = fractions.Fraction(3, 1)
DOTTED_WHOLE_NOTE = fractions.Fraction(3, 2)
DOTTED_HALF_NOTE = fractions.Fraction(3, 4)
DOTTED_QUARTER_NOTE = fractions.Fraction(3, 8)
DOTTED_EIGHT_NOTE = fractions.Fraction(3, 16)
DOTTED_SIXTEENTH_NOTE = fractions.Fraction(3, 32)
DOTTED_THIRTY_SECOND_NOTE = fractions.Fraction(3, 64)
DOTTED_SIXTY_FOURTH_NOTE = fractions.Fraction(3, 128)
DOTTED_HUNDRED_TWENTY_NOTE = fractions.Fraction(3, 256)
DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = fractions.Fraction(3, 512)

DOUBLE_DOTTED_LARGE_NOTE = fractions.Fraction(14, 1)
DOUBLE_DOTTED_LONG_NOTE = fractions.Fraction(7, 1)
DOUBLE_DOTTED_DOUBLE_WHOLE_NOTE = fractions.Fraction(7, 2)
DOUBLE_DOTTED_WHOLE_NOTE = fractions.Fraction(7, 4)
DOUBLE_DOTTED_HALF_NOTE = fractions.Fraction(7, 8)
DOUBLE_DOTTED_QUARTER_NOTE = fractions.Fraction(7, 16)
DOUBLE_DOTTED_EIGHT_NOTE = fractions.Fraction(7, 32)
DOUBLE_DOTTED_SIXTEENTH_NOTE = fractions.Fraction(7, 64)
DOUBLE_DOTTED_THIRTY_SECOND_NOTE = fractions.Fraction(7, 128)
DOUBLE_DOTTED_SIXTY_FOURTH_NOTE = fractions.Fraction(7, 256)
DOUBLE_DOTTED_HUNDRED_TWENTY_NOTE = fractions.Fraction(7, 512)
DOUBLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = fractions.Fraction(7, 1024)

TRIPLE_DOTTED_LARGE_NOTE = fractions.Fraction(15, 1)
TRIPLE_DOTTED_LONG_NOTE = fractions.Fraction(15, 2)
TRIPLE_DOTTED_DOUBLE_WHOLE_NOTE = fractions.Fraction(15, 4)
TRIPLE_DOTTED_WHOLE_NOTE = fractions.Fraction(15, 8)
TRIPLE_DOTTED_HALF_NOTE = fractions.Fraction(15, 16)
TRIPLE_DOTTED_QUARTER_NOTE = fractions.Fraction(15, 32)
TRIPLE_DOTTED_EIGHT_NOTE = fractions.Fraction(15, 64)
TRIPLE_DOTTED_SIXTEENTH_NOTE = fractions.Fraction(15, 128)
TRIPLE_DOTTED_THIRTY_SECOND_NOTE = fractions.Fraction(15, 256)
TRIPLE_DOTTED_SIXTY_FOURTH_NOTE = fractions.Fraction(15, 512)
TRIPLE_DOTTED_HUNDRED_TWENTY_NOTE = fractions.Fraction(15, 1024)
TRIPLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = fractions.Fraction(15, 2048)


DEFAULT_GROUPINGS = {
    #FOUR_FOUR_METRE: [HALF_NOTE, HALF_NOTE],
    FOUR_FOUR_METRE: 4 * [QUARTER_NOTE],
    THREE_FOUR_METRE: [QUARTER_NOTE, QUARTER_NOTE, QUARTER_NOTE],
    TWO_FOUR_METRE: [QUARTER_NOTE, QUARTER_NOTE],
    SIX_EIGHT_METRE: [DOTTED_QUARTER_NOTE, DOTTED_QUARTER_NOTE]
}
"""dict: Metre (Fraction) -> Common note grouping (list)."""

BEAM_CHARACTERS = [
    '     ',
    '┌─┬─┐',
    '╒═╤═╕',

    #[' ', ' ', ' ', ' ', ' '],
    #['┌', '─', '┬', '─', '┐'],
    #['╒', '═', '╤', '═', '╕'],
    #['┌\n╞', '─\n═', '┬\n╪', '─\n═', '┐\n╡'],
    #['╒\n╞', '═\n═', '╤\n╪', '═\n═', '╕\n╡'],
]
"""list: Number of beams (int) -> Beam characters (str)."""

STEM = ' │'
"""str: Note stem."""

DOT = '.'
"""str: Dot character for dotted notes."""

BLACK_CIRCLE = '●'
"""str: Filled note head character."""

WHITE_CIRCLE = '○'
"""str: Empty note head character."""

BEAM_NUMBER = collections.defaultdict(int, {
    EIGHT_NOTE: 1,
    DOTTED_EIGHT_NOTE: 1,
    DOUBLE_DOTTED_EIGHT_NOTE: 1,
    TRIPLE_DOTTED_EIGHT_NOTE: 1,

    SIXTEENTH_NOTE: 2,
    DOTTED_SIXTEENTH_NOTE: 2,
    DOUBLE_DOTTED_SIXTEENTH_NOTE: 2,
    TRIPLE_DOTTED_SIXTEENTH_NOTE: 2,

    THIRTY_SECOND_NOTE: 3,
    DOTTED_THIRTY_SECOND_NOTE: 3,
    DOUBLE_DOTTED_THIRTY_SECOND_NOTE: 3,
    TRIPLE_DOTTED_THIRTY_SECOND_NOTE: 3,

    SIXTY_FOURTH_NOTE: 4,
    DOTTED_SIXTY_FOURTH_NOTE: 4,
    DOUBLE_DOTTED_SIXTY_FOURTH_NOTE: 4,
    TRIPLE_DOTTED_SIXTY_FOURTH_NOTE: 4,
})
"""defaultdict: Note (Fraction) -> Number of beams (int)."""


BEAM_START = 0
BEAM_CONTINUATION = 1
BEAM_END = 2
"""int: Beam directions."""


def dot_note(note, n=1):
    """Augment note value. Add next briefer note. n-times."""
    if n == 0:
        return note

    if n < 0:
        return dedot_note(note, n=-n)

    return (2 * 2**n - 1) * note / (2 ** n)


def dedot_note(note, n=1):
    """Inverse of dot_note."""
    if n == 0:
        return note

    if n < 0:
        return dot_note(note, n=-n)

    return (2 ** n) * note / (2 * 2**n - 1)


def _print_all_notes():
    """Print all possible note values."""
    noteNames = {
        'Large Note' : fractions.Fraction(8, 1),
        'Long Note' : fractions.Fraction(4, 1),
        'Double Whole Note' : fractions.Fraction(2, 1),
        'Whole Note' : fractions.Fraction(1, 1),
        'Half Note' : fractions.Fraction(1, 2),
        'Quarter Note' : fractions.Fraction(1, 4),
        'Eight Note' : fractions.Fraction(1, 8),
        'Sixteenth Note' : fractions.Fraction(1, 16),
        'Thirty-Second Note' : fractions.Fraction(1, 32),
        'Sixty-Fourth Note' : fractions.Fraction(1, 64),
        'Hundred-Twenty Note' : fractions.Fraction(1, 128),
        'Two Hundred Fifty-Sixth Note' : fractions.Fraction(1, 256),
    }

    def name_2_var(name):
        name = name.replace('-', ' ')
        name = name.replace(' ', '_')
        name = name.upper()
        return name

    dotteds = [('', 0), ('DOTTED_', 1), ('DOUBLE_DOTTED_', 2), ('TRIPLE_DOTTED_', 3)]
    for prefix, n in dotteds:
        for name, note in noteNames.items():
            var = prefix + name_2_var(name)
            dottedNote = dot_note(note, n)
            print(var, '= fractions.Fraction(%d, %d)' % (dottedNote.numerator, dottedNote.denominator))


def text_size(text):
    """Size of text.

    Usage:
        >>> text_size('abc\nde')
        (3, 2)
    """
    lines = text.splitlines()
    widths = map(len, lines)
    width = max(widths, default=0)
    height = len(lines)
    return width, height


def heighten_text(text, height, fill=' '):
    """Heighten text to a given height. Add additional empty space atop if
    necessary.

    Usage:
        >>> print(heighten_text('a', 3, '?'))
        ?
        ?
        a
    """
    w, h = text_size(text)
    return (height - h) * (w * fill + '\n') + text


def hstack(*texts, sep=''):
    """Stack text blocks horizontally."""
    heights = [text_size(txt)[1] for txt in texts]
    height = max(heights, default=0)
    segments = [heighten_text(txt, height).splitlines() for txt in texts]
    return '\n'.join(
        sep.join(row) for row in zip(*segments)
    )


def note_head(note):
    """Get note head."""
    return '%s%s' % (
        WHITE_CIRCLE if note > QUARTER_NOTE else BLACK_CIRCLE,
        DOT if note.numerator == 3 else ' '
    )


def note_beam(note, beamDirection=BEAM_START):
    """Get top part of note stem with beam."""
    nBeams = BEAM_NUMBER[note]
    if nBeams == 0:
        if note > HALF_NOTE:
            return '  '

        return STEM

    chars = BEAM_CHARACTERS[nBeams]
    if beamDirection == BEAM_START:
        beam = ' ' + chars[0]

    elif beamDirection == BEAM_CONTINUATION:
        beam = chars[1:3]

    elif beamDirection == BEAM_END:
        beam = chars[3:]

    return beam


def format_note(note, beamDirection=BEAM_START):
    """Format note.

    Usage:
        >>> print(format_note(EIGHT_NOTE))
         ┌
         │
        ●

    Args:
        note (Fraction): Note value.

    Kwargs:
        beamDirection (int): Either BEAM_START, BEAM_CONTINUATION or BEAM_END.

    Returns:
        str: Note string.
    """
    stem = STEM if note <= HALF_NOTE else '  '
    return '\n'.join([
        note_beam(note, beamDirection),
        stem,
        note_head(note),
    ])


def _cumsum(notes):
    """Generator for cumsum."""
    pos = fractions.Fraction()
    for note in notes:
        yield pos
        pos += note


def cumsum(notes):
    """Note cumsum. Starting from zero."""
    return list(_cumsum(notes))


def expand(notes):
    """Expand note fractions to the same denominator."""
    denominator = max(n.denominator for n in notes)
    for note in notes:
        num = note.numerator * denominator / note.denominator
        assert int(num) == num, 'Can not expand fractions to same denominator!'
        yield fractions.Fraction(
            int(num),
            denominator,
            _normalize=False,
        )


def sum_grouping(grouping):
    """Sum fractions together while not normalizing them.

    Usage:
        >>> print(sum_grouping([HALF_NOTE, HALF_NOTE]))
        '2/2'  # And not '1/1'!
    """
    notes = list(expand(grouping))
    denominator = notes[0].denominator
    return fractions.Fraction(
        sum(note.numerator for note in notes),
        denominator,
        _normalize=False,
    )


def _beam_needs_to_end(position, note, metre, groupCrossings):
    """Check if beam needs to end for a given note at a certain position.

    Args:
        position (Fraction): Note position.
        note (Fraction): Note value.
        metre (Fraction): Bar duration.
        groupCrossings (Fraction): Group crossings.

    Returns:
        bool: Beam needs to end.
    """
    if note >= QUARTER_NOTE:
        return True

    # Map to bar level
    start = position % metre
    end = (start + note) % metre

    # Wrap around / end of bar
    if end < start:
        return True

    # Check group crossings
    for crossing in groupCrossings:
        if start < crossing <= end:
            return True

    return False


def format_time_signature(grouping):
    """Format time signature. Metre or grouping.

    Usage:
        >>> print(format_time_signature(FOUR_FOUR_METRE))
        4
        -
        4

        >>> print(format_time_signature([3*EIGHT_NOTE, 2*EIGHT_NOTE, 2*EIGHT_NOTE]))
        3+2+2
        -----
          8
    """
    try:
        metre = sum_grouping(grouping)
    except TypeError:
        metre = grouping

    if is_complex(metre):
        grouping = expand(grouping)
        num = '+'.join(map(str, (g.numerator for g in grouping)))
    else:
        num = str(metre.numerator)

    den = str(metre.denominator)
    width = max(map(len, (num, den)))
    return hstack('\n'.join([
        num.center(width),
        width * '-',
        den.center(width),
    ]), ' ')


def _empty_space(nBeams=0):
    chars = BEAM_CHARACTERS[nBeams]
    return '\n'.join([
        chars[1],
        ' ',
        ' ',
    ])


def format_notes(notes, grouping=None, metre=FOUR_FOUR_METRE, strech=True,
                 timeSignature=True):
    """Format notes.

    Args:
        notes (list): Notes to format.

    Kwargs:
        grouping (list): Note grouping for beam formatting. Overrides metre. If
            non given, default will be taken via metre.
        metre (Fraction): Time signature.
        strech (bool): Stretch whitespace between notes according to their
            playing time. (Not implemented yet).
        timeSignature (bool): Prepend time signature to output.

    Returns:
        str: Formatted notes.
    """
    if min(notes) < SIXTEENTH_NOTE:
        raise ValueError('Sub 1/16 notes not supported!')

    if grouping is None:
        grouping = DEFAULT_GROUPINGS[metre]
    else:
        metre = sum_grouping(grouping)

    groupCrossings = cumsum(grouping)
    """list: Points inside a bar where notes cross over to another group. Beams
    need to be resetted.
    """

    raster = min(notes)

    segments = []
    if timeSignature:
        segments.append(format_time_signature(grouping))

    pos = fractions.Fraction()
    beaming = False
    barNr = 0
    for note in notes:
        # Add bar line for new bars
        currentBarNr = int(pos / metre)
        for _ in range(currentBarNr - barNr):
            segments.append('\n'.join(3 * [' │ ']))
            barNr += 1

        # Determine beam direction
        if _beam_needs_to_end(pos, note, metre, groupCrossings):
            beamDir = BEAM_END
            beaming = False
        elif beaming:
            beamDir = BEAM_CONTINUATION
        else:
            beamDir = BEAM_START
            beaming = True

        # Render note
        txt = format_note(note, beamDirection=beamDir)
        segments.append(txt)

        # Widen Notenbild
        if beamDir == BEAM_END:
            nBeams = 0
        else:
            nBeams = BEAM_NUMBER[note]

        emptySpace = _empty_space(nBeams)
        segments.append(emptySpace)

        if strech:
            for _  in range(int(note / raster) - 1):
                segments.append(emptySpace)

        pos += note

    return hstack(*segments)


if __name__ == '__main__':
    _print_all_notes()
