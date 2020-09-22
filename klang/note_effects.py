"""All kind of note message effects."""
from typing import Deque, Tuple, Generator
import collections
import time

from klang.messages import Note
from klang.block import Block
from klang.connections import MessageInput, MessageOutput


class NoteLengthener(Block):

    """Convert note-ons to actual notes (note-on followed by a note-off later on
    in the future).
    """

    clock = time.time
    """callable: Clock giver."""

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
