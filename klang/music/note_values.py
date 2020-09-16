"""Musical note values."""
from fractions import Fraction
from typing import Sequence


__all__ = [
    'LARGE_NOTE', 'LONG_NOTE', 'DOUBLE_WHOLE_NOTE', 'WHOLE_NOTE', 'HALF_NOTE',
    'QUARTER_NOTE', 'EIGHT_NOTE', 'SIXTEENTH_NOTE', 'THIRTY_SECOND_NOTE',
    'SIXTY_FOURTH_NOTE', 'HUNDRED_TWENTY_NOTE', 'TWO_HUNDRED_FIFTY_SIXTH_NOTE',

    'DOTTED_LARGE_NOTE', 'DOTTED_LONG_NOTE', 'DOTTED_DOUBLE_WHOLE_NOTE',
    'DOTTED_WHOLE_NOTE', 'DOTTED_HALF_NOTE', 'DOTTED_QUARTER_NOTE',
    'DOTTED_EIGHT_NOTE', 'DOTTED_SIXTEENTH_NOTE', 'DOTTED_THIRTY_SECOND_NOTE',
    'DOTTED_SIXTY_FOURTH_NOTE', 'DOTTED_HUNDRED_TWENTY_NOTE',
    'DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE',

    'DOUBLE_DOTTED_LARGE_NOTE', 'DOUBLE_DOTTED_LONG_NOTE',
    'DOUBLE_DOTTED_DOUBLE_WHOLE_NOTE', 'DOUBLE_DOTTED_WHOLE_NOTE',
    'DOUBLE_DOTTED_HALF_NOTE', 'DOUBLE_DOTTED_QUARTER_NOTE',
    'DOUBLE_DOTTED_EIGHT_NOTE', 'DOUBLE_DOTTED_SIXTEENTH_NOTE',
    'DOUBLE_DOTTED_THIRTY_SECOND_NOTE', 'DOUBLE_DOTTED_SIXTY_FOURTH_NOTE',
    'DOUBLE_DOTTED_HUNDRED_TWENTY_NOTE',
    'DOUBLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE',

    'TRIPLE_DOTTED_LARGE_NOTE', 'TRIPLE_DOTTED_LONG_NOTE',
    'TRIPLE_DOTTED_DOUBLE_WHOLE_NOTE', 'TRIPLE_DOTTED_WHOLE_NOTE',
    'TRIPLE_DOTTED_HALF_NOTE', 'TRIPLE_DOTTED_QUARTER_NOTE',
    'TRIPLE_DOTTED_EIGHT_NOTE', 'TRIPLE_DOTTED_SIXTEENTH_NOTE',
    'TRIPLE_DOTTED_THIRTY_SECOND_NOTE', 'TRIPLE_DOTTED_SIXTY_FOURTH_NOTE',
    'TRIPLE_DOTTED_HUNDRED_TWENTY_NOTE',
    'TRIPLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE',

    'dot_note', 'dedot_note', 'Tuplet',
]


"""Note value definitions."""


LARGE_NOTE = Fraction(8, 1)
LONG_NOTE = Fraction(4, 1)
DOUBLE_WHOLE_NOTE = Fraction(2, 1)
WHOLE_NOTE = Fraction(1, 1)
HALF_NOTE = Fraction(1, 2)
QUARTER_NOTE = Fraction(1, 4)
EIGHT_NOTE = Fraction(1, 8)
SIXTEENTH_NOTE = Fraction(1, 16)
THIRTY_SECOND_NOTE = Fraction(1, 32)
SIXTY_FOURTH_NOTE = Fraction(1, 64)
HUNDRED_TWENTY_NOTE = Fraction(1, 128)
TWO_HUNDRED_FIFTY_SIXTH_NOTE = Fraction(1, 256)

DOTTED_LARGE_NOTE = Fraction(12, 1)
DOTTED_LONG_NOTE = Fraction(6, 1)
DOTTED_DOUBLE_WHOLE_NOTE = Fraction(3, 1)
DOTTED_WHOLE_NOTE = Fraction(3, 2)
DOTTED_HALF_NOTE = Fraction(3, 4)
DOTTED_QUARTER_NOTE = Fraction(3, 8)
DOTTED_EIGHT_NOTE = Fraction(3, 16)
DOTTED_SIXTEENTH_NOTE = Fraction(3, 32)
DOTTED_THIRTY_SECOND_NOTE = Fraction(3, 64)
DOTTED_SIXTY_FOURTH_NOTE = Fraction(3, 128)
DOTTED_HUNDRED_TWENTY_NOTE = Fraction(3, 256)
DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = Fraction(3, 512)

DOUBLE_DOTTED_LARGE_NOTE = Fraction(14, 1)
DOUBLE_DOTTED_LONG_NOTE = Fraction(7, 1)
DOUBLE_DOTTED_DOUBLE_WHOLE_NOTE = Fraction(7, 2)
DOUBLE_DOTTED_WHOLE_NOTE = Fraction(7, 4)
DOUBLE_DOTTED_HALF_NOTE = Fraction(7, 8)
DOUBLE_DOTTED_QUARTER_NOTE = Fraction(7, 16)
DOUBLE_DOTTED_EIGHT_NOTE = Fraction(7, 32)
DOUBLE_DOTTED_SIXTEENTH_NOTE = Fraction(7, 64)
DOUBLE_DOTTED_THIRTY_SECOND_NOTE = Fraction(7, 128)
DOUBLE_DOTTED_SIXTY_FOURTH_NOTE = Fraction(7, 256)
DOUBLE_DOTTED_HUNDRED_TWENTY_NOTE = Fraction(7, 512)
DOUBLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = Fraction(7, 1024)

TRIPLE_DOTTED_LARGE_NOTE = Fraction(15, 1)
TRIPLE_DOTTED_LONG_NOTE = Fraction(15, 2)
TRIPLE_DOTTED_DOUBLE_WHOLE_NOTE = Fraction(15, 4)
TRIPLE_DOTTED_WHOLE_NOTE = Fraction(15, 8)
TRIPLE_DOTTED_HALF_NOTE = Fraction(15, 16)
TRIPLE_DOTTED_QUARTER_NOTE = Fraction(15, 32)
TRIPLE_DOTTED_EIGHT_NOTE = Fraction(15, 64)
TRIPLE_DOTTED_SIXTEENTH_NOTE = Fraction(15, 128)
TRIPLE_DOTTED_THIRTY_SECOND_NOTE = Fraction(15, 256)
TRIPLE_DOTTED_SIXTY_FOURTH_NOTE = Fraction(15, 512)
TRIPLE_DOTTED_HUNDRED_TWENTY_NOTE = Fraction(15, 1024)
TRIPLE_DOTTED_TWO_HUNDRED_FIFTY_SIXTH_NOTE = Fraction(15, 2048)


def dot_note(note: Fraction, n: int = 1) -> Fraction:
    """Augment note value. Add next briefer note. n-times."""
    if n == 0:
        return note

    if n < 0:
        return dedot_note(note, n=-n)

    return (2 * 2**n - 1) * note / (2 ** n)


def dedot_note(note: Fraction, n: int = 1) -> Fraction:
    """Inverse of dot_note."""
    if n == 0:
        return note

    if n < 0:
        return dot_note(note, n=-n)

    return (2 ** n) * note / (2 * 2**n - 1)


def _print_all_notes():
    """Print all possible note values."""
    noteNames = {
        'Large Note' : Fraction(8, 1),
        'Long Note' : Fraction(4, 1),
        'Double Whole Note' : Fraction(2, 1),
        'Whole Note' : Fraction(1, 1),
        'Half Note' : Fraction(1, 2),
        'Quarter Note' : Fraction(1, 4),
        'Eight Note' : Fraction(1, 8),
        'Sixteenth Note' : Fraction(1, 16),
        'Thirty-Second Note' : Fraction(1, 32),
        'Sixty-Fourth Note' : Fraction(1, 64),
        'Hundred-Twenty Note' : Fraction(1, 128),
        'Two Hundred Fifty-Sixth Note' : Fraction(1, 256),
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
            print(var, '= Fraction(%d, %d)' % (dottedNote.numerator, dottedNote.denominator))


class Tuplet(Fraction):

    """Tuplet note container."""

    NAMES = {
        2: 'Duplet',
        3: 'Triplet',
        4: 'Quadruplet',
        5: 'Quintuplet',
        6: 'Sextuplet',
        7: 'Septuplet',
        8: 'Octuplet',
        9: 'Nontuplet',
    }

    def __new__(cls, num: int, notes: Sequence[Fraction], den: int = None):
        if den is None:
            den = num - 1  # Seems to be the default case in music

        totalNoteValue = sum(notes)
        return super().__new__(cls, totalNoteValue * den / num)

    def __init__(self, num: int, notes: Sequence[Fraction], den: int = None):
        if den is None:
            den = num - 1  # Seems to be the default case in music

        self.num = num
        self.notes = notes
        self.den = den

    def __str__(self):
        name = self.NAMES.get(self.num, self.__class__.__name__)
        return '%s(%s:%s)' % (name, self.num, self.den)


if __name__ == '__main__':
    _print_all_notes()
