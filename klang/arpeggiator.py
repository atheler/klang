"""Arpeggiator and helpers."""
import bisect
import collections
import functools
import random
import time

from klang.audio.oscillators import Phasor
from klang.audio.sequencer import pizza_slice_number
from klang.block import Block
from klang.composite import Composite
from klang.connections import MessageInput, MessageRelay, MessageOutput


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

    up = 1
    down = -1
    if order == 'upDown':
        return [first, up]

    if order == 'downUp':
        return [last, down]

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
        dst = alternate(i + 1, length)
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
        jump = alternating_jump_sequence(length)
        return [jump[position % length]]

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


class Arpeggio(Block):
    def __init__(self, order='up', initialNotes=[]):
        super().__init__()
        assert order in {
            'up', 'down', 'upDown', 'downUp', 'random', 'alternating',
        }
        self.order = order
        self.notes = []
        self.state = initial_arpeggio_state(length=len(self.notes), order=order)
        self.inputs = [MessageInput(owner=self), MessageInput(owner=self)]
        self.trigger = self.inputs[1]
        self.outputs = [MessageOutput(owner=self)]
        for note in initialNotes:
            self.add_note(note)

    def add_note(self, newNote):
        """Add a new note to the arpeggio. Will be in-sorted accordingly. Should
        be a note-on (but we do not assert).
        """
        # Check if we already have pitch registered
        for note in self.notes:
            if note.pitch == newNote.pitch:
                return

        bisect.insort(self.notes, newNote)

    def remove_note(self, note):
        """Remove / deactivate a note in the arpeggio."""
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

    def process_notes(self, *notes):
        for note in notes:
            self.process_note(note)

    def update(self):
        for note in self.input.receive():
            self.process_note(note)
            print('Got note', note)

        for nr in self.trigger.receive():
            arpNote = next(self)
            if arpNote is None:
                continue

            self.output.send(arpNote)

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
        return '%s(%d notes)' % (type(self).__name__, len(self.notes))


class Pulsar(Block):
    def __init__(self, frequency, nSteps, initialPhase=0.):
        super().__init__()
        self.nSteps = nSteps
        self.currentNr = -1
        self.outputs = [MessageOutput(owner=self)]
        self.phasor = Phasor(frequency, initialPhase)

    def increment(self):
        self.currentNr = (self.currentNr + 1) % self.nSteps

    def update(self):
        self.phasor.update()
        phase = self.phasor.output.value
        nr = pizza_slice_number(phase, self.nSteps)
        for _ in range(nr - self.currentNr):
            self.increment()
            self.output.send(self.currentNr)

    def __str__(self):
        return '%s(%.1f Hz, %d steps)' % (
            type(self).__name__,
            self.phasor.frequency,
            self.nSteps,
        )


class CircularDiscretizer(Block):
    def __init__(self, nSteps):
        super().__init__(nInputs=1)
        self.nSteps = nSteps
        self.outputs = [MessageOutput(owner=self)]
        self.currentNr = -1

    def increment(self):
        self.currentNr = (self.currentNr + 1) % self.nSteps

    def update(self):
        phase = self.input.value
        nr = pizza_slice_number(phase, self.nSteps)
        diff = (nr - self.currentNr) % self.nSteps
        for _ in range(diff):
            self.increment()
            self.output.send(self.currentNr)


class NoteLengthener(Block):

    clock = time.time

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.activeNotes = collections.deque()
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]

    def outdated_notes(self, now):
        """Iterate over outdated notes."""
        while self.activeNotes:
            end, note = self.activeNotes[0]  # Peek
            if now < end:
                return

            yield note
            self.activeNotes.popleft()

    def update(self):
        now = self.clock()
        for note in self.outdated_notes(now):
            noteOff = note.silence()
            self.output.send(noteOff)

        for note in self.input.receive():
            if note.off:
                continue

            entry = (now + self.duration, note)
            self.activeNotes.append(entry)
            self.output.send(note)


class Arpeggiator(Composite):

    """Note arpeggiator block."""

    def __init__(self, frequency, nSteps, order='up', duration=.1):
        super().__init__()
        self.inputs = [MessageRelay(owner=self)]
        self.outputs = [MessageRelay(owner=self)]

        # Init internal blocks
        phasor = Phasor(frequency)
        discretizer = CircularDiscretizer(nSteps)
        self.arpeggio = Arpeggio(order)
        noteLengthener = NoteLengthener(duration)

        # Make connections of internal notes
        self.input.connect(self.arpeggio.input)
        self.arpeggio.output.connect(noteLengthener.input)
        noteLengthener.output.connect(self.output)
        phasor.output.connect(discretizer.input)
        discretizer.output.connect(self.arpeggio.trigger)

        self.update_internal_exec_order()
