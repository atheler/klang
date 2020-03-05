"""Music sequencer."""
import collections

import numpy as np
import matplotlib.pyplot as plt

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.blocks import Block
from klang.connections import MessageOutput
from klang.constants import TAU
from klang.messages import Note
from klang.music.metre import FOUR_FOUR
from klang.music.tempo import bar_period


DEFAULT_PATTERN = np.zeros(16)
DT = 1. / SAMPLING_RATE


SKIP = -1


def angular_velocity(tempo, metre=FOUR_FOUR):
    """Calculate angular bar velocity for given tempo in BPM."""
    return TAU / bar_period(tempo, metre)


class Sequencer(Block):

    """Sequencer for pattern playback with an output per pattern line.

    TODO:
      - Proper / useful way to do sequencing?
      - Pattern SKIP value (aka. multiple currentPhases).
      - Micro rhythms.
    """

    def __init__(self, pattern=DEFAULT_PATTERN, tempo=120., noteDuration=.5,
                 microRhythm=None):
        self.pattern = np.atleast_2d(pattern)
        super().__init__()
        self.outputs = [
            MessageOutput(owner=self) for _ in range(self.nChannels)
        ]
        self.tempo = tempo
        self.noteDuration = noteDuration
        self.microRhythm = microRhythm

        self.currentPhase = 0.
        self.activeNotes = collections.deque()
        self.prevIndex = None

    @property
    def nChannels(self):
        return self.pattern.shape[0]

    @property
    def nSteps(self):
        return self.pattern.shape[1]

    def phase_2_index(self, phase):
        """Get buffer index given bar phase."""
        idx = int(phase / TAU * self.nSteps)
        return idx % self.nSteps

    def turn_off_outdated_notes(self):
        """Send note-off messages for outdated notes."""
        while self.activeNotes:
            end, channel, note = self.activeNotes[0]  # Peek
            if self.currentPhase < end:
                break

            noteOff = Note(pitch=note.pitch, velocity=0.)
            self.outputs[channel].send(noteOff)
            self.activeNotes.popleft()

    def update(self):
        self.turn_off_outdated_notes()
        idx = int(self.currentPhase % TAU * self.nSteps) % self.nSteps

        if idx != self.prevIndex:
            dt = TAU / self.nSteps
            for channel, value in enumerate(self.pattern.T[idx]):
                if value:
                    note = Note(pitch=value, velocity=1.)
                    self.outputs[channel].send(note)
                    self.activeNotes.append(
                        (self.currentPhase + dt, channel, note)
                    )

            self.prevIndex = idx

        omega = angular_velocity(self.tempo)
        self.currentPhase += DT * BUFFER_SIZE * omega

    def __str__(self):
        return '%s(%.1f BPM, %d channels, %d steps)' % (
            self.__class__.__name__,
            self.tempo,
            self.nChannels,
            self.nSteps,
        )


if __name__ == '__main__':
    duration = 4.
    pattern = [
        [ 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 ],
        [ 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0 ],
        [ 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0 ],
    ]

    seq = Sequencer(pattern)
    print(seq)

    length = int(duration * SAMPLING_RATE)
    #t = DT * np.arange(length)

    for i in range(length // BUFFER_SIZE):
        seq.update()
        for out in seq.outputs:
            queue = out.get_value()
            while queue:
                print(queue.popleft())

    plt.show()
