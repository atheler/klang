import os
import sys
import fractions

sys.path.append(os.getcwd())
from klang.music.note_values import QUARTER_NOTE
from klang.music.note_formatting import format_notes, format_tuplet
from klang.music.note_values import EIGHT_NOTE, DOTTED_EIGHT_NOTE, SIXTEENTH_NOTE, HALF_NOTE
from klang.music.note_values import Tuplet

cases = [
    4 * [QUARTER_NOTE],
    8 * [EIGHT_NOTE],
    16 * [SIXTEENTH_NOTE],
    [ QUARTER_NOTE, EIGHT_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, DOTTED_EIGHT_NOTE, SIXTEENTH_NOTE, ],
    [SIXTEENTH_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE],
    [SIXTEENTH_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE],
    [EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE],
    [QUARTER_NOTE, QUARTER_NOTE, EIGHT_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE],
]


for notes in cases:
    print(format_notes(notes))
    print()


print('Complex metre:')
notes = 2 * 7 * [EIGHT_NOTE]
print(format_notes(notes, grouping=[3 * EIGHT_NOTE, 2 * EIGHT_NOTE, 2 * EIGHT_NOTE]))
print()


print('Tuplets:')
triplet = Tuplet(3, 3 * [EIGHT_NOTE])
print(format_tuplet(triplet))
print()


print(format_notes([
    QUARTER_NOTE, triplet, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, QUARTER_NOTE,
]))
print()


print(format_notes([
    HALF_NOTE,
    Tuplet(5, 5 * [EIGHT_NOTE]),
    QUARTER_NOTE,
]))
print()


print(format_notes([
    Tuplet(5, 5 * [EIGHT_NOTE]),
    Tuplet(7, 7 * [EIGHT_NOTE]),
]))
print()


print(format_notes([
    Tuplet(3, 3 * [QUARTER_NOTE]),
    Tuplet(3, 3 * [QUARTER_NOTE]),
    Tuplet(3, 3 * [HALF_NOTE]),
]))
print()


print('Nested tuplet')
print(format_notes([
    Tuplet(3, [
        Tuplet(3, 3*[EIGHT_NOTE]),
        Tuplet(5, 5*[SIXTEENTH_NOTE]),
        Tuplet(3, 3*[EIGHT_NOTE]),
    ]),
]))
print()


notes=[
    Tuplet(6, [
        Tuplet(3, 3 * [EIGHT_NOTE]),
        SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE,
        Tuplet(5, 5 * [SIXTEENTH_NOTE]),
    ])
]
print(format_notes(notes, grouping=[
    fractions.Fraction(3, 8),
    fractions.Fraction(2, 8),
]))
print()
