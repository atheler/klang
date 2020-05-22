"""Arpeggiator and helpers.

An arpeggio is playing individual chord notes sequentially
(https://en.wikipedia.org/wiki/Arpeggio). This can happen in different orders
and dictates the state dimensions. One dimensional for simpler patterns, two
dimensional for the bit more complex (see initial_arpeggio_state(...)).
"""
import bisect
import functools
import random

from klang.audio.oscillators import Phasor
from klang.sequencer import pizza_slice_number, PizzaSlicer
from klang.block import Block
from klang.composite import Composite
from klang.connections import MessageInput, MessageRelay, MessageOutput
from klang.note_effects import NoteLengthener


ARPEGGIO_ORDERS = [
    'up',
    'down',
    'upDown',
    'downUp',
    'random',
    'alternating',
]
"""list: All supported arpeggio orders."""


def initial_arpeggio_state(length, order):
    """Get initial arpeggiator state. Depending on the order we need a one ore
    two dimensional state (e.g. simply up or alternating vs. upDown).

    Args:
        length (int): Number of notes in arpeggio.
        order (str): Arpeggio note order.

    Returns:
        list: Initial arpeggio state vector.
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
    """Calculate next arpeggiator state.

    Args:
        state (list): Arpeggio state.
        length (int): Number of notes.
        order (str): Arpeggio order.

    Returns:
        list: Arpeggio state vector.
    """
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

    raise ValueError('Unknown arpeggio note order %r!' % order)


class Arpeggio(Block):

    """Arpeggio container. Can receive new notes in trigger the next arpeggio
    note when triggered.

    Attributes:
        order (str): Arpeggio order.
        notes (list): Current note in the arpeggio.
        state (list): Current arpeggio state.
    """

    def __init__(self, order='up', initialNotes=[]):
        if order not in ARPEGGIO_ORDERS:
            raise ValueError('Invalid order %r!' % order)

        super().__init__()
        self.inputs = _, self.trigger = [
            MessageInput(owner=self),
            MessageInput(owner=self),
        ]
        self.outputs = [MessageOutput(owner=self)]
        self.order = order
        self.notes = []
        self.state = initial_arpeggio_state(length=len(self.notes), order=order)
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
        """Process single note."""
        if note.on:
            self.add_note(note)
        else:
            self.remove_note(note)

    def process_notes(self, *notes):
        """Process multiple notes at once."""
        for note in notes:
            self.process_note(note)

    def update(self):
        for note in self.input.receive():
            self.process_note(note)

        for _ in self.trigger.receive():
            arpNote = next(self)
            if arpNote:
                self.output.send(arpNote)

    def __next__(self):
        """Get next note to play from arpeggiator."""
        if not self.notes:
            return

        currentNote = self.notes[self.state[0]]
        self.state = step_arpeggio_state(
            self.state,
            length=len(self.notes),
            order=self.order
        )
        return currentNote

    def __str__(self):
        return '%s(%d notes)' % (type(self).__name__, len(self.notes))


class Pulsar(Block):

    """Pulsar / clock block.

    Outputs discrete trigger messages for each step.
    """

    def __init__(self, frequency, nSteps, initialPhase=0.):
        super().__init__()
        self.nSteps = nSteps
        self.currentNr = -1
        self.outputs = [MessageOutput(owner=self)]
        self.phasor = Phasor(frequency, initialPhase)

    def increment(self):
        """Go to next step."""
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


class Arpeggiator(Composite):

    """Note arpeggiator block."""

    def __init__(self, frequency, nSteps, order='up', duration=.1):
        """Args:
            frequency (float): Arpeggio frequency.
            nSteps (int): Number of steps (?)

        Kwargs:
            order (str): Arpeggio order.
            duration (float): Note duration.
        """
        super().__init__()
        self.inputs = [MessageRelay(owner=self)]
        self.outputs = [MessageRelay(owner=self)]

        # Init internal blocks
        phasor = Phasor(frequency)
        pizzaSlicer = PizzaSlicer(nSteps)
        self.arpeggio = Arpeggio(order)
        noteLengthener = NoteLengthener(duration)

        # Make connections of internal notes
        self.input.connect(self.arpeggio.input)
        self.arpeggio.output.connect(noteLengthener.input)
        noteLengthener.output.connect(self.output)
        phasor.output.connect(pizzaSlicer.input)
        pizzaSlicer.output.connect(self.arpeggio.trigger)

        self.update_internal_exec_order()
