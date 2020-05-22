"""Music sequencer."""
import itertools
import random

from klang.audio.oscillators import Phasor
from klang.block import Block
from klang.composite import Composite
from klang.connections import MessageInput, MessageOutput, MessageRelay, Relay
from klang.constants import TAU
from klang.math import is_divisible
from klang.messages import Note
from klang.music.metre import FOUR_FOUR_METRE, number_of_beats
from klang.music.tempo import bar_period
from klang.note_effects import NoteLengthener


__all__ = [
    'random_pattern', 'pizza_slice_number', 'PizzaSlicer', 'PatternLookup',
    'Sequencer',
]


def random_pattern(length, period=None, minVal=60, maxVal=72):
    """Generate random sequence for given length with cycle period.

    Args:
        length (int): Pattern length.

    Kwargs:
        period (int): Repetition cycle inside the patter (<length).
        minVal (int): Minimum pattern value.
        maxVal (int): Maximum pattern value.

    Returns:
        list: Random pattern.
    """
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
    """Get slice number for a given angle and a total number of pieces.

    Args:
        angle (float): Phase value.
        nSlices (int): Number of pizza slice.

    Returns:
        int: Pizza slice number.
    """
    return int((angle % TAU) / TAU * nSlices)


class PizzaSlicer(Block):

    """Circular phase edge detector. Input phase -> discrete index messages."""

    def __init__(self, nSlices):
        super().__init__(nInputs=1)
        self.outputs = [MessageOutput(owner=self)]
        self.nSlices = nSlices
        self.currentIdx = -1

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

    """Lookup pitch numbers in pattern list and output Note messages."""

    def __init__(self, pattern):
        super().__init__()
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.pattern = pattern

    def update(self):
        for nr in self.input.receive():
            pitch = self.pattern[nr]
            if pitch:
                note = Note(pitch=pitch, velocity=1.)
                self.output.send(note)

    def __str__(self):
        return '%s(pattern: %s)' % (type(self).__name__, self.pattern)


class Sequence(Composite):

    """Single channel sequencer."""

    def __init__(self, sequencer, pattern, tempo=120., relNoteDuration=.5,
                 metre=FOUR_FOUR_METRE, beatValue=None):
        """Args:
            sequencer (Sequencer): Parent sequencer container.
            pattern (list): Sequence pattern.

        Kwargs:
            tempo (float): Tempo in beats per minute.
            relNoteDuration (float): Note duration relative to step duration.
            metre (Fraction): Time signature.
            beatValue (Fraction): Beat value.

        """
        self.validate_pattern(pattern, metre, beatValue)
        super().__init__()
        self.inputs = self.phaseIn, = [Relay(owner=self)]
        self.outputs = _, self.phaseOut = [MessageRelay(owner=self), Relay(owner=self)]
        self.sequencer = sequencer
        self.pattern = pattern

        barPeriod = bar_period(tempo, metre, beatValue)
        phasor = Phasor(frequency=1. / barPeriod)
        pizza = PizzaSlicer(nSlices=self.nSteps)
        lookup = PatternLookup(pattern)
        absNoteDuration = relNoteDuration * barPeriod / self.nSteps
        noteLengthener = NoteLengthener(duration=absNoteDuration)

        phasor.output.connect(self.phaseOut)
        self.phaseOut.connect(self.phaseIn)
        self.phaseIn.connect(pizza.input)

        pizza.output.connect(lookup.input)
        lookup.output.connect(noteLengthener.input)
        noteLengthener.output.connect(self.output)

        self.update_internal_exec_order()

    @property
    def nSteps(self):
        """Number of sequence steps."""
        return len(self.pattern)

    @staticmethod
    def validate_pattern(pattern, metre, beatValue=None):
        """Validate pattern. Does it fit on the metre?"""
        nBeats = number_of_beats(metre, beatValue)
        if not is_divisible(len(pattern), nBeats):
            msg = 'Can not map pattern %s onto metre' % pattern
            raise ValueError(msg)

    def apply_micro_rhythm(self, microRhythm=None):
        """Apply micro rhythm to sequence."""
        # Disconnect phaseOut / phaseIn
        if self.phaseOut.connected:
            for dst in list(self.phaseOut.outgoingConnections):  # Mutate while iterating
                self.phaseOut.disconnect(dst)

        if self.phaseIn.connected:
            src = self.phaseIn.incomingConnection
            src.disconnect(self.phaseIn)

        # Patch microRhythm
        if microRhythm:
            self.phaseOut | microRhythm | self.phaseIn
        else:
            self.phaseOut | self.phaseIn

        self.sequencer.update_internal_exec_order()

    def reset_micro_rhythm(self):
        """Reset micro rhythm."""
        self.apply_micro_rhythm(microRhythm=None)


class Sequencer(Composite):

    """Pattern sequencer."""

    def __init__(self, pattern, *args, **kwargs):
        super().__init__()
        self.pattern = pattern
        self.sequences = []
        for row in pattern:
            self.add_channel(row, *args, **kwargs)

    def add_channel(self, *args, **kwargs):
        """Add a new sequence channel."""
        sequence = Sequence(sequencer=self, *args, **kwargs)
        self.sequences.append(sequence)
        relay = MessageRelay(owner=self)
        sequence.output.connect(relay)
        self.outputs.append(relay)
        self.update_internal_exec_order()

    @property
    def nChannels(self):
        """Number of channels."""
        return len(self.pattern)

    def apply_micro_rhythm(self, channel, microRhythm):
        """Apply micro to sequence of channel."""
        seq = self.sequences[channel]
        seq.apply_micro_rhythm(microRhythm)
