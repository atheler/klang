"""All kind of note message effects."""
from typing import Deque, Tuple, Generator
import collections

from klang.block import Block
from klang.clock import ClockMixin
from klang.connections import MessageInput, MessageOutput
from klang.messages import Note


class NoteLengthener(Block, ClockMixin):

    """Convert note-ons to actual notes (note-on followed by a note-off later on
    in the future).
    """

    def __init__(self, duration: float):
        """Args:
            duration (float): Absolute note duration in seconds.
        """
        super().__init__()
        self.duration = duration
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.activeNotes: Deque[Tuple[float, Note]] = collections.deque()

    def outdated_notes(self, now: float) -> Generator[Note, None, None]:
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
            if note.on:
                entry = (now + self.duration, note)
                self.activeNotes.append(entry)
                self.output.send(note)


class MaxNotes(Block):

    """Manages an maximum number of active notes. Old notes will be deactivated
    by sending out note-off messages.
    """

    def __init__(self, nNotes=1):
        super().__init__()
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.nNotes = nNotes
        self.activeNotes = collections.deque([], maxlen=nNotes + 1)

    def update(self):
        for newNote in self.input.receive():
            if newNote.on:
                self.activeNotes.append(newNote)
                while len(self.activeNotes) > self.nNotes:
                    oldNote = self.activeNotes.popleft()
                    self.output.send(oldNote.silence())

                self.output.send(newNote)


class MessageMixer(Block):

    """Combines received messages and sends them to output."""

    def __init__(self, nInputs=2):
        super().__init__()
        self.outputs = [MessageOutput(owner=self)]
        for _ in range(nInputs):
            self.add_new_channel()

    def add_new_channel(self):
        """Add a new message input."""
        self.inputs.append(MessageInput(owner=self))

    def update(self):
        for input_ in self.inputs:
            for msg in input_.receive():
                self.output.send(msg)
