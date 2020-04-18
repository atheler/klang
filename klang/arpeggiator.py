import bisect
import functools
import random


def initial_arpeggio_state(length, order):
    """Get initial arpeggiator state. Depending on the order we need a one ore
    two dimensional state (e.g. simply up or alternating vs. upDown).

    Args:
        length (int): Number of notes in arpeggio.
        order (str): Arpeggio note order.
    """
    first = 0
    last = length - 1
    if order == 'up':
        return [first]

    if order == 'down':
        return [last]

    if order == 'upDown':
        return [first, 1]

    if order == 'downUp':
        return [last, -1]

    if order == 'random':
        return [random.randint(first, last)]

    if order == 'alternating':
        return [first]

    raise ValueError('Unknown arpeggio note order %r!' % order)


def alternate(n, length):
    """Indices of alternating note order. Index -> number.

    Illustration for 4 notes:

      Notes
        ^
        |     B
        |             G
        |         E
        | C
        ----------------> Time

    Usage:
        >>> for i in range(10):
        ...     print(alternate(i, length=5))
        0
        4
        1
        3
        2
        0
        4
        1
        3
        2
    """
    n = n % length
    if n % 2 == 0:
        return (n // 2) % length
    else:
        return (-n // 2) % length


assert alternate(-1, length=5) == 2
assert alternate(0, length=5) == 0
assert alternate(1, length=5) == 4
assert alternate(2, length=5) == 1
assert alternate(3, length=5) == 3
assert alternate(4, length=5) == 2
assert alternate(5, length=5) == 0


assert alternate(-1, length=4) == 2
assert alternate(0, length=4) == 0
assert alternate(1, length=4) == 3
assert alternate(2, length=4) == 1
assert alternate(3, length=4) == 2
assert alternate(4, length=4) == 0


@functools.lru_cache()
def alternating_jump_sequence(length):
    """Get jump index array for alternating pattern."""
    table = length * [0]
    for i in range(length):
        src = alternate(i, length)
        dst = alternate(i+1, length)
        table[src] = dst

    return table

    """
    # Same function. More cryptic.
    half = length // 2
    if length % 2 == 0:
        half -= 1

    left = list(range(length-1, half, -1))
    right = list(range(half, 0, -1))
    return left + [0] + right
    """


def step_arpeggio_state(state, length, order):
    """Calculate next arpeggiator state."""
    if order == 'random':
        return initial_arpeggio_state(length, order='random')

    position = state[0]
    if order == 'up':
        return [(position + 1) % length]
    if order == 'down':
        return [(position - 1) % length]
    if order == 'alternating':
        position %= length
        jump = alternating_jump_sequence(length)
        return [jump[position]]

    first = 0
    last = length - 1
    velocity = state[1]
    if order in {'upDown', 'downUp'}:
        if (
            (position == last and velocity > 0)  # Reached top
            or (position == first and velocity < 0)  # Reached bottom
        ):
            velocity *= -1  # Turn around
        return [(position + velocity) % length, velocity]


class Arpeggio:
    def __init__(self, order='up', initialNotes=[]):
        assert order in {
            'up', 'down', 'upDown', 'downUp', 'random', 'alternating',
        }
        self.order = order
        self.notes = []
        self.state = initial_arpeggio_state(length=len(self.notes), order=order)
        for note in initialNotes:
            self.add_note(note)

    def add_note(self, newNote):
        # Check if we already have pitch registered
        for note in self.notes:
            if note.pitch == newNote.pitch:
                return

        bisect.insort(self.notes, newNote)

    def remove_note(self, note):
        for i, oldNote in enumerate(self.notes):
            if oldNote.pitch == note.pitch:
                break
        else:  # If no break
            return

        self.notes.remove(oldNote)

        # Roll back arpeggiator state if necessary
        if self.state[0] > i:
            self.state[0] -= 1

        self.state[0] %= len(self.notes)

    def process_note(self, note):
        if note.on:
            self.add_note(note)
        else:
            self.remove_note(note)

    def __next__(self):
        """Get next note to play from arpeggiator."""
        if not self.notes:
            return

        currentNote = self.notes[self.state[0]]
        self.state = step_arpeggio_state(
            state=self.state,
            length=len(self.notes),
            order=self.order
        )
        return currentNote

    def __str__(self):
        return '%s(%d notes)' % (type(self).__name__, len(self))
