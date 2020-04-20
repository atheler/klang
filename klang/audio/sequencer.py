"""Music sequencer."""
import collections
import itertools
import random
import time

from klang.audio import INTERVAL
from klang.block import Block
from klang.connections import MessageInput, MessageOutput
from klang.constants import TAU
from klang.math import is_divisible
from klang.messages import Note
from klang.music.metre import FOUR_FOUR_METRE, number_of_beats
from klang.music.tempo import bar_period


def random_pattern(length, period=None, minVal=60, maxVal=72):
    """Generate random sequence for given length with cycle period."""
    if period is None:
        period = length

    cycle = itertools.cycle([
        random.randint(minVal, maxVal) for _ in range(period)
    ])
    seq = []
    while len(seq) < length:
        seq.append(next(cycle))

    return seq


def pizza_slice_number(angle, nSlices):
    """Get slice number for a given angle and a total number of pieces."""
    return int((angle % TAU) / TAU * nSlices)


class Phasor(Block):
    def __init__(self, frequency=1.):
        super().__init__(nOutputs=1)
        self.frequency = frequency
        self.currentPhase = 0.

    def update(self):
        phase = self.currentPhase
        self.output.set_value(phase)
        self.currentPhase = (TAU * self.frequency * INTERVAL + phase) % TAU


class PizzaSlicer(Block):

    """Circular phase edge detector. Input phase -> discrete index messages."""

    def __init__(self, nSlices):
        super().__init__(nInputs=1)
        self.nSlices = nSlices
        self.currentIdx = -1
        self.outputs = [MessageOutput(owner=self)]

    def increment(self):
        """Increment current index by one."""
        self.currentIdx = (self.currentIdx + 1) % self.nSlices

    def update(self):
        phase = self.input.value
        idx = pizza_slice_number(phase, self.nSlices)
        missing = (idx - self.currentIdx) % self.nSlices
        for _ in range(missing):
            self.increment()
            self.output.send(self.currentIdx)

    def __str__(self):
        return '%s(nSlices: %s)' % (type(self).__name__, self.nSlices)


class PatternLookup(Block):

    """Pattern lookup. Index -> Note generator. Also note-off via note
    duration.
    """

    clock = time.time

    def __init__(self, pattern, noteDuration=.1234):
        super().__init__()
        self.pattern = pattern
        self.noteDuration = noteDuration
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.activeNotes = collections.deque()

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
            noteOff = note._replace(velocity=0.)
            self.output.send(noteOff)

        for msg in self.input.receive():
            value = self.pattern[msg]
            if not value:
                continue

            note = Note(pitch=value, velocity=1.)
            self.activeNotes.append((now + self.noteDuration, note))
            self.output.send(note)

    def __str__(self):
        return '%s(%s, noteDuration: %.1f)' % (
            type(self).__name__,
            self.pattern,
            self.noteDuration,
        )


class Sequence(Block):

    """Single channel sequence.

    Three internal blocks with optional external MicroRhythm:

        Phasor  ->  PizzaSlicer -> PatternLookup.
               |  ^
               v  |
            MicroRhythm
    """

    def __init__(self, pattern, tempo=120., relNoteDuration=.5,
                 metre=FOUR_FOUR_METRE, beatValue=None):
        """Args:
            pattern (list): Sequence pattern.

        Kwargs:
            tempo (float): Beats per minute.
            relNoteDuration (float): Note duration relative to cell size.
            metre (Fraction): Time signature.
            beatValue (Fraction): Beat value.
        """
        self.validate_pattern(pattern, metre, beatValue)
        super().__init__()

        # Phasor
        barPeriod = bar_period(tempo, metre, beatValue)
        self.phasor = Phasor(frequency=1. / barPeriod)

        # Pizza slicer
        nSteps = len(pattern)
        self.pizza = PizzaSlicer(nSlices=nSteps)
        self.phasor.output.connect(self.pizza.input)

        # Lookup
        absNoteDuration = relNoteDuration * barPeriod / nSteps
        self.lookup = PatternLookup(pattern, absNoteDuration)
        self.pizza.output.connect(self.lookup.input)
        self.outputs = [self.lookup.output]  # Alias output

    @property
    def nSteps(self):
        """Number of steps."""
        return self.lookup.pattern.shape[0]

    @staticmethod
    def validate_pattern(pattern, metre, beatValue=None):
        """Validate pattern. Does it fit on the metre?"""
        nBeats = number_of_beats(metre, beatValue)
        if not is_divisible(len(pattern), nBeats):
            msg = 'Can not map pattern %s onto metre' % pattern
            raise ValueError(msg)

    def connect_micro_rhythm(self, microRhythm):
        """Insert micro rhythm block between phasor and PizzaSlicer."""
        self.phasor.output.disconnect(self.pizza.input)
        self.phasor.output.connect(microRhythm.input)
        microRhythm.output.connect(self.pizza.input)

    def update(self):
        pass  # Do nothing! Update is taken care of via the output connection!

    def __str__(self):
        return '%s(pattern: %s)' % (type(self).__name__, self.lookup.pattern)


class Sequencer(Block):

    """Multi channel sequencer.

    TODO:
      - Phasor sync?
    """

    def __init__(self, pattern, *args, **kwargs):
        super().__init__()
        self.sequences = [Sequence(ptr, *args, **kwargs) for ptr in pattern]
        self.outputs = [seq.output for seq in self.sequences]

    @property
    def nChannels(self):
        """Number of channels."""
        return len(self.sequences)

    def update(self):
        pass  # Do nothing! Update is taken care of via the output connections!

    def __str__(self):
        return '%s(channels: %d)' % (type(self).__name__, self.nChannels)
