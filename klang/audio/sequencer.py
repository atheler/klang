"""Music sequencer."""
import collections
import itertools
import random

import numpy as np
import matplotlib.pyplot as plt

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.audio import DT
from klang.block import Block
from klang.connections import MessageOutput
from klang.constants import TAU
from klang.messages import PitchNote
from klang.music.tempo import angular_velocity


DEFAULT_PATTERN = np.zeros(16)
PASS_THROUGH = lambda phase: phase


def pie_slice_number(angle, nPieces):
    """Get slice segment index for a given angle and number of pieces."""
    return int((angle % TAU) / TAU * nPieces)


class Sequencer(Block):

    """Sequencer for pattern playback with an output per pattern line.

    TODO:
      - Proper / useful way to do sequencing?
      - Pattern SKIP value (aka. multiple currentPhases).
      - Micro rhythms.
    """

    def __init__(self, pattern=DEFAULT_PATTERN, tempo=120., noteDuration=.5,
                 microRhythm=PASS_THROUGH):
        #assert 0 <= noteDuration <= 1
        super().__init__()
        self.pattern = np.atleast_2d(pattern)
        self.tempo = tempo
        self.noteDuration = noteDuration
        self.microRhythm = microRhythm

        self.outputs = [
            MessageOutput(owner=self) for _ in range(len(pattern))
        ]
        self.currentPhase = 0.
        self.prevIndex = None
        self.activeNotes = collections.deque()

    @property
    def nChannels(self):
        """Number of channels."""
        return self.pattern.shape[0]

    @property
    def nSteps(self):
        """Number of sequencer steps."""
        return self.pattern.shape[1]

    def turn_off_outdated_notes(self):
        """Send note-off messages for outdated notes."""
        while self.activeNotes:
            end, channel, note = self.activeNotes[0]  # Peek
            if self.currentPhase < end:
                break

            noteOff = PitchNote(pitch=note.pitch, velocity=0.)
            self.outputs[channel].send(noteOff)
            self.activeNotes.popleft()

    def update(self):
        self.turn_off_outdated_notes()
        #phase = self.microRhythm(self.currentPhase)
        phase = self.currentPhase
        idx = pie_slice_number(phase, self.nSteps)
        if idx != self.prevIndex:
            dt = TAU / self.nSteps
            for channel, value in enumerate(self.pattern.T[idx]):
                if value > 0:
                    note = PitchNote(pitch=value, velocity=1.)
                    self.outputs[channel].send(note)
                    self.activeNotes.append(
                        (self.currentPhase + self.noteDuration * dt, channel, note)
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


def random_sequence(length, period=None, minVal=60, maxVal=72):
    """Generate random sequence for given length with cycle period."""
    if period is None:
        period = length

    cycle = itertools.cycle([random.randint(minVal, maxVal) for _ in range(period)])
    seq = []
    while len(seq) < length:
        seq.append(next(cycle))

    return seq