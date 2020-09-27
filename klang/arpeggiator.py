"""Arpeggio and Arpeggiator.

An arpeggio is playing individual chord notes sequentially
(https://en.wikipedia.org/wiki/Arpeggio). This can happen in different orders.
"""
from typing import List
import bisect
import collections
import itertools
import math
import random

from klang.audio.oscillators import Phasor
from klang.composite import Composite
from klang.connections import MessageInput, MessageOutput
from klang.messages import Note
from klang.music.tempo import compute_duration


VALID_ORDERS = ['up', 'down', 'upDown', 'downUp', 'alternating', 'random']
"""Possible arpeggio orders."""


def validate_order(order):
    """Validate arpeggio order."""
    if order not in VALID_ORDERS:
        possibilities = ', '.join(map(repr, VALID_ORDERS))
        raise ValueError(f'Invalid order {order!r}! Either: {possibilities}.')


def interleave(first, second):
    """Interleave two lists with each other. If they are not of equal length
    extend with the excess elements of the longer lists.
    """
    commonLength = min(len(first), len(second))
    ret = list(itertools.chain(*zip(first[:commonLength], second[:commonLength])))
    ret.extend(first[commonLength:])
    ret.extend(second[commonLength:])
    return ret


def arpeggio_index_permutation(order, length):
    """Index permutations for different arpeggio orders and lengths."""
    validate_order(order)
    if length == 1:
        return [0]

    upwards = list(range(length))
    downwards = list(reversed(upwards))
    if order == 'up':
        return upwards

    if order == 'down':
        return downwards

    if order == 'upDown':
        return upwards[:-1] + downwards[:-1]

    if order == 'downUp':
        return downwards[:-1] + upwards[:-1]

    if order == 'alternating':
        # Alternating note order like:
        # 'abc01' -> ['a', '0', 'b', '1', 'c']
        halfway = int(math.ceil(.5 * length))
        lower = upwards[:halfway]
        upper = upwards[halfway:]
        return interleave(lower, list(reversed(upper)))

    if order == 'random':
        permut = list(range(length))
        random.shuffle(permut)
        return permut


class Arpeggio(collections.abc.Sequence):

    """Note arpeggio container. Holds multiple notes and cycles through them for
    different orderings.

    Attributes:
        order: Arpeggio note order.
        notes: Current arpeggio notes.
        permutation: Current to note index mapping.
    """

    def __init__(self, order: str = 'up', initialNotes: List[Note] = None):
        """Kwargs:
            order: Arpeggio play order.
            initialNotes: Initial music notes.
        """
        validate_order(order)
        self.order = order
        self.notes: List[Note] = []
        self.permutation: List[int] = []
        self.current = 0
        if initialNotes:
            for note in initialNotes:
                self.add_note(note)

    def wrap_current(self):
        """Wrap current index around corresponding the active permutation."""
        length = len(self.permutation)
        if length == 0:
            self.current = 0
        else:
            self.current %= length

    def update_state(self):
        """Update internal arpeggio state."""
        permut = arpeggio_index_permutation(self.order, len(self))
        self.permutation = permut
        self.wrap_current()

    def add_note(self, note: Note):
        """Add new note to arpeggio."""
        if note not in self:
            bisect.insort(self.notes, note)
            self.update_state()

    def remove_note(self, note: Note):
        """Remove note from arpeggio."""
        for n in self:
            if n.pitch == note.pitch:
                self.notes.remove(n)
                self.update_state()
                break
        else:
            raise ValueError('No note with pitch %d in Arpeggio' % note.pitch)

    def __getitem__(self, index):
        return self.notes[index]

    def __len__(self):
        return len(self.notes)

    def __contains__(self, note):
        return any(note.pitch == n.pitch for n in self.notes)

    def __next__(self):
        """Return the next arpeggio note."""
        if not self:
            raise StopIteration

        #if self.order == 'random':
        #    return random.choice(self.notes)

        idx = self.permutation[self.current]
        self.current += 1
        self.wrap_current()
        return self[idx]

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            self.notes,
        )


class Arpeggiator(Composite):
    def __init__(self, interval=.1, *args, **kwargs):
        super().__init__()
        interval = compute_duration(interval)
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.prevPhase = 0.
        self.prevNote = None
        self.phasor = Phasor(1./interval)
        self.arpeggio = Arpeggio(*args, **kwargs)

    def update(self):
        for newNote in self.input.receive():
            if newNote.on:
                self.arpeggio.add_note(newNote)
            elif newNote in self.arpeggio:
                self.arpeggio.remove_note(newNote)

        self.phasor.update()
        phase = self.phasor.output.value
        if phase <= self.prevPhase:
            if self.prevNote:
                noteOff = self.prevNote.silence()
                self.output.send(noteOff)

            if self.arpeggio:
                note = next(self.arpeggio)
                self.output.send(note)
                self.prevNote = note

        self.prevPhase = phase
