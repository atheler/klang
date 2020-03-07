import os
import sys

sys.path.append(os.getcwd())
from klang.music.note_values import QUARTER_NOTE, format_notes
from klang.music.note_values import EIGHT_NOTE, DOTTED_EIGHT_NOTE, SIXTEENTH_NOTE


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

notes = 2 * 7 * [EIGHT_NOTE]
print(format_notes(notes, grouping=[3 * EIGHT_NOTE, 2 * EIGHT_NOTE, 2 * EIGHT_NOTE]))
