"""Musical note values.


TODO:
  - How to format more complex note formations? Like:


 ┌──┐
 │  │
●  ●

    3
 ┌──┬──┐
 │  │  │
●  ●  ●


 ╒══╤══╤══╕
 │  │  │  │
●  ●  ●  ● 


 ┌──╤══╕
 │  │  │
●  ●  ● 


 ╒═─┬─═╕    ╒──┬──╕
 │  │  │ OR │  │  │
●  ●  ●    ●  ●  ● 


 ┌─═╤──┐
 │  │  │
●  ●  ● 


 ┌──╤══╤──┐
 │  │  │  │
●  ●  ●  ● 


 ┌──╤══╤──┬─═╕
 │  │  │  │  │
●  ●  ●  ●  ● 


Frame elements:
 ┌──┬──┐  ╔══╦══╗  ╒══╤══╕
 │  │  │  ║  ║  ║  │  │  │
●  ●  ●  ●  ●  ●  ●  ●  ● 


"""
import sys
import fractions


NOTE_NAMES = {
    fractions.Fraction(8, 1): 'Large Note',
    fractions.Fraction(4, 1): 'Long Note',
    fractions.Fraction(2, 1): 'Double Whole Note',
    fractions.Fraction(1, 1): 'Whole Note',
    fractions.Fraction(1, 2): 'Half Note',
    fractions.Fraction(1, 4): 'Quarter Note',
    fractions.Fraction(1, 8): 'Eight Note',
    fractions.Fraction(1, 16): 'Sixteenth Note',
    fractions.Fraction(1, 32): 'Thirty-Second Note',
    fractions.Fraction(1, 64): 'Sixty-Fourth Note',
    fractions.Fraction(1, 128): 'Hundred-Twenty Note',
    fractions.Fraction(1, 256): 'Two Hundred Fifty-Sixth Note',
}
"""dict: Note value (Fraction) -> Note name (str)."""


NOTE_SYMBOLS = {
    fractions.Fraction(1, 1): ('  \n'
                               '  \n'
                               '○ '),
    fractions.Fraction(1, 2): (' │\n'
                               ' │\n'
                               '○ '),
    fractions.Fraction(1, 4): (' │\n'
                               ' │\n'
                               '● '),
    fractions.Fraction(1, 8): (' ┌\n'
                               ' │\n'
                               '● '),
    fractions.Fraction(1, 16): (' ╒\n'
                                ' │\n'
                                '● '),
}
"""dict: Note value (Fraction) -> String note representation (str)."""


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


def _add_doted_note_values():
    """Add dotted, double dotted and triple dotted versions of notes to
    NOTE_NAMES dictionary.
    """
    for noteValue, noteName in dict(NOTE_NAMES).items():
        dottedNote = dot_note(noteValue)
        NOTE_NAMES[dottedNote] = 'Dotted ' + noteName
        doubleDottedNote = dot_note(dottedNote)
        NOTE_NAMES[doubleDottedNote] = 'Double Dotted ' + noteName
        trippleDottedNote = dot_note(doubleDottedNote)
        NOTE_NAMES[trippleDottedNote] = 'Triple Dotted ' + noteName


def _add_notes_to_module():
    """Take all notes from NOTE_NAMES and add them to module as attributes."""
    module = sys.modules[__name__]
    for noteValue, noteName in NOTE_NAMES.items():
        varName = noteName.replace('-', ' ')
        varName = varName.replace(' ', '_')
        varName = varName.upper()

        setattr(module, varName, noteValue)


_add_doted_note_values()
_add_notes_to_module()


def format_note(note):
    """Format single note."""
    if not note in NOTE_SYMBOLS:
        raise ValueError

    return NOTE_SYMBOLS[note]


def format_notes(notes, sep=' '):
    """Format multiple notes."""
    rows = [[], [], []]
    for note in notes:
        for line, row in zip(format_note(note).split('\n'), rows):
            row.append(line)

    return '\n'.join(sep.join(row) for row in rows)


if __name__ == '__main__':
    notes = [
            WHOLE_NOTE,
            HALF_NOTE,
            QUARTER_NOTE,
            EIGHT_NOTE,
            SIXTEENTH_NOTE
    ]
    print(format_notes(notes))
