"""Music sequencer."""
from fractions import Fraction
from typing import List, Union
import collections
import itertools
import random

import numpy as np

from klang.audio.oscillators import Phasor
from klang.block import Block
from klang.composite import Composite
from klang.connections import MessageInput, MessageOutput, MessageRelay, Relay
from klang.constants import TAU
from klang.messages import Note
from klang.music.note_values import QUARTER_NOTE, SIXTEENTH_NOTE
from klang.music.rhythm import MicroRhyhtm
from klang.music.tempo import tempo_2_period
from klang.note_effects import NoteLengthener


__all__ = [
    'random_pattern', 'pizza_slice_number', 'PizzaSlicer', 'PatternLookup',
    'Sequencer',
]


Pattern = Union[List[int], np.ndarray]


def random_pattern(length: int, period: int = None, minVal: int = 60, maxVal:
                   int = 72) -> Pattern:
    """Generate random sequence for given length with cycle period.

    Args:
        length: Pattern length.

    Kwargs:
        period: Repetition cycle inside the patter (<length).
        minVal: Minimum pattern value.
        maxVal: Maximum pattern value.

    Returns:
        list: Random pattern.
    """
    if period is None:
        period = length

    cycle = itertools.cycle([
        random.randint(minVal, maxVal) for _ in range(period)
    ])
    pattern: List[int] = []
    while len(pattern) < length:
        pattern.append(next(cycle))

    return pattern


def pizza_slice_number(angle: float, nSlices: int) -> int:
    """Get slice number for a given angle and a total number of pieces.

    Args:
        angle (float): Phase value.
        nSlices (int): Number of pizza slice.

    Returns:
        int: Pizza slice number.
    """
    return int((angle % TAU) / TAU * nSlices)


def atleast_1d(obj) -> Pattern:
    """Assure 1d list. Pack obj in list if necessary. Similar to
    numpy.atleast_1d but support for different length lists.
    """
    if isinstance(obj, np.ndarray):
        return np.atleast_1d(obj)

    if not isinstance(obj, collections.abc.Sequence):
        obj = [obj]

    return obj


def atleast_2d(obj) -> Pattern:
    """Assure 2d list. Pack obj in list if necessary. Similar to
    numpy.atleast_2d but support for different length lists.
    """
    if isinstance(obj, np.ndarray):
        return np.atleast_2d(obj)

    obj = atleast_1d(obj)
    if not isinstance(obj[0], collections.abc.Sequence):
        obj = [obj]

    return obj


class PizzaSlicer(Block):

    """Circular phase edge detector.

    Maps float input phase [0, TAU) to discrete index output messages (depending
    on how many steps).
    """

    def __init__(self, nSlices: int):
        """Args:
            nSlices: Number of pizza slices / steps.
        """
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

    def __init__(self, pattern: Pattern):
        super().__init__()
        self.inputs = [MessageInput(owner=self)]
        self.outputs = [MessageOutput(owner=self)]
        self.pattern = pattern

    def update(self):
        for nr in self.input.receive():
            # TODO: Support for chords
            pitch = self.pattern[nr]
            if pitch:
                note = Note(pitch=pitch, velocity=1.)
                self.output.send(note)

    def __str__(self):
        return '%s(%s)' % (type(self).__name__, self.pattern)


class Sequence(Composite):

    """Single channel sequence."""

    def __init__(self, sequencer, pattern: Pattern, tempo: float = 120,
                 beatValue: Fraction = QUARTER_NOTE, grid: Fraction =
                 SIXTEENTH_NOTE, relNoteLength: float = .5, absNoteLength: float
                 = None):
        """Args:
            sequencer: Parent sequencer.
            pattern: Pitch pattern to sequence.

        Kwargs:
            tempo: Beats per minute.
            beatValue: For tempo definition.
            grid: Pattern grid duration.
            relNoteLength: Note length relative to grid cell.
            absNoteLength: Absolute length note duration. Overrites relNoteLength.
        """
        super().__init__()
        self.sequencer = sequencer
        self.pattern = atleast_1d(pattern)
        self.tempo = tempo
        self.beatValue = beatValue
        self.grid = grid

        self.inputs = self.phaseIn, = [Relay(owner=self)]
        self.outputs = _, self.phaseOut = [MessageRelay(owner=self), Relay(owner=self)]

        if absNoteLength is None:
            absNoteLength = relNoteLength * self.duration / self.length

        self.phasor = Phasor(frequency=1. / self.duration)
        self.pizza = PizzaSlicer(self.length)
        self.lookup = PatternLookup(self.pattern)
        self.lengthener = NoteLengthener(absNoteLength)

        self.phasor | self.phaseOut
        self.phaseOut.connect(self.phaseIn)
        self.phaseIn | self.pizza | self.lookup | self.lengthener | self.output
        self.update_internal_exec_order(self.phasor, self.pizza)

    @property
    def length(self) -> int:
        """Pattern length."""
        return len(self.pattern)

    @property
    def duration(self) -> float:
        """Sequence duration for current tempo."""
        return self.length * self.grid / self.beatValue * tempo_2_period(self.tempo)

    def disconnect_phase_insert(self):
        """Disconnect phaseOut & phaseIn connections."""
        for dst in set(self.phaseOut.outgoingConnections):
            self.phaseOut.disconnect(dst)

        if self.phaseIn.connected:
            src = self.phaseIn.incomingConnection
            src.disconnect(self.phaseIn)

    def apply_micro_rhythm(self, microRhythm: MicroRhyhtm):
        """Patch microRhythm to sequence."""
        self.disconnect_phase_insert()
        self.phaseOut | microRhythm | self.phaseIn
        self.sequencer.update_internal_exec_order()

    def reset_micro_rhythm(self):
        """Dispatch microRhythm from sequence."""
        self.disconnect_phase_insert()
        self.phaseOut.connect(self.phaseIn)
        self.sequencer.update_internal_exec_order()

    def __str__(self):
        infos = [
            str(self.pattern),
            'tempo=%.1f BPM' % self.tempo,
            'beatValue=%s' % self.beatValue,
            'grid=%s' % self.grid,
        ]

        return '%s(%s)' % (
            type(self).__name__,
            ', '.join(infos)
        )


class Sequencer(Composite):

    """Pattern sequencer."""

    def __init__(self, pattern: Pattern, *args, **kwargs):
        """See Sequence (not Sequencer) for help."""
        super().__init__()
        self.pattern = atleast_2d(pattern)
        self.sequences: List[Sequence] = []
        for row in self.pattern:
            self.add_channel(row, *args, **kwargs)

    def add_channel(self, *args, **kwargs):
        """Add a new sequence channel."""
        newSeq = Sequence(self, *args, **kwargs)
        self.sequences.append(newSeq)
        relay = MessageRelay(owner=self)
        newSeq.output.connect(relay)
        self.outputs.append(relay)
        self.update_internal_exec_order()

    @property
    def nChannels(self) -> int:
        """Number of channels."""
        return len(self.pattern)

    def apply_micro_rhythm(self, microRhythm, channel):
        """Apply micro rhythm to all or one specific sequence(s)."""
        seq = self.sequences[channel]
        seq.apply_micro_rhythm(microRhythm)

    def reset_micro_rhythm(self, channel):
        """Reset micro rhythm from all or one specific sequence(s)."""
        seq = self.sequences[channel]
        seq.reset_micro_rhythm()

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            'nChannels=%d' % self.nChannels,
        )
