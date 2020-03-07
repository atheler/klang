"""Musical note values.

TODO:
  - Note formatting -> in its own module (?).
"""
import fractions

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


class Tuplet(fractions.Fraction):

    """Tuplet note container."""

    """
    NAMES = {
        3: 'Triplet',
        5: 'Quintuplet',
        6: 'Sextuplet',
        7: 'Septuplet',
    }
    """

    def __new__(cls, num, notes, den=None):
        if den is None:
            den = num - 1  # Seems to be the default case in music

        totalNoteValue = sum(notes)
        return super().__new__(cls, totalNoteValue * den / num)

    def __init__(self, num, notes, den=None):
        if den is None:
            den = num - 1  # Seems to be the default case in music

        self.num = num
        self.notes = notes
        self.den = den

    def __str__(self):
        return 'Tuplet(%s:%s)' % (self.num, self.den)


if __name__ == '__main__':
    _print_all_notes()
