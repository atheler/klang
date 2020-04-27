"""All kind of note message effects."""
import time
import collections

from klang.block import Block
from klang.connections import MessageInput, MessageOutput


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
