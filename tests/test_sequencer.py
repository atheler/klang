import unittest

import numpy as np
from numpy.testing import assert_equal

from klang.block import Block
from klang.connections import MessageInput
from klang.constants import TAU
from klang.sequencer import (
    PizzaSlicer,
    Sequence,
    Sequencer,
    atleast_1d,
    atleast_2d,
)
from klang.music.note_values import QUARTER_NOTE, SIXTEENTH_NOTE


SIXTEEN_STEPS = list(range(16))


class TestAtLeast(unittest.TestCase):
    def test_atleast_1d(self):
        self.assertEqual(atleast_1d(0), [0])
        self.assertEqual(atleast_1d([0, 1, 2, 3]), [0, 1, 2, 3])
        self.assertEqual(atleast_1d([[0, 1, 2, 3]]), [[0, 1, 2, 3]])

    def test_atleast_1d_with_numpy_array(self):
        assert_equal(atleast_1d(np.array(0)), [0])
        assert_equal(atleast_1d(np.array([0, 1, 2, 3])), [0, 1, 2, 3])
        assert_equal(atleast_1d(np.array([[0, 1, 2, 3]])), [[0, 1, 2, 3]])

    def test_atleast_2d(self):
        self.assertEqual(atleast_2d(0), [[0]])
        self.assertEqual(atleast_2d([0, 1, 2, 3]), [[0, 1, 2, 3]])
        self.assertEqual(atleast_2d([[[0, 1, 2, 3]]]), [[[0, 1, 2, 3]]])

    def test_atleast_2d_with_numpy_array(self):
        assert_equal(atleast_2d(np.array(0)), [[0]])
        assert_equal(atleast_2d(np.array([0, 1, 2, 3])), [[0, 1, 2, 3]])
        assert_equal(atleast_2d(np.array([[0, 1, 2, 3]])), [[0, 1, 2, 3]])


class TestPizzaSlicer(unittest.TestCase):
    def setUp(self):
        self.receiver = MessageInput()

    def compare_messages(self, messages=None):
        if not messages:
            return self.assertEqual(len(self.receiver.queue), 0)

        for received, msg in zip(self.receiver.receive(), messages):
            self.assertEqual(received, msg)

    def test_start_index(self):
        pizza = PizzaSlicer(16)
        pizza | self.receiver

        self.assertEqual(pizza.currentIdx, -1)

        pizza.update()

        self.assertEqual(pizza.currentIdx, 0)
        self.compare_messages([0])

    def test_pattern_of_four(self):
        pizza = PizzaSlicer(4)
        pizza | self.receiver
        cases = [
            (.0 * TAU, [0]),
            (.25 * TAU - .1, None),
            (.25 * TAU, [1]),
            (.25 * TAU + .1, None),
            (.50 * TAU, [2]),
            (.75 * TAU, [3]),
            (1.0 * TAU - .1, None),
            (1.0 * TAU + .1, [0]),
        ]
        for phase, messages in cases:
            pizza.input.set_value(0.)
            pizza.update()
            self.compare_messages(messages)

    def test_double_jump(self):
        """Multiple pizza slice jumps at once."""

        pizza = PizzaSlicer(4)
        pizza | self.receiver
        cases = [
            (.0 * TAU, [0]),
            (.50 * TAU, [1, 2]),
            (1.0 * TAU, [3, 0]),
        ]
        for phase, messages in cases:
            pizza.input.set_value(0.)
            pizza.update()
            self.compare_messages(messages)


class TestSequence(unittest.TestCase):
    def test_properties_with_different_patterns(self):
        seq = Sequence(None, SIXTEEN_STEPS, tempo=120, beatValue=QUARTER_NOTE, grid=SIXTEENTH_NOTE)

        self.assertEqual(seq.length, 16)
        self.assertEqual(seq.duration, 2.0)

        seq = Sequence(None, SIXTEEN_STEPS, tempo=100, beatValue=QUARTER_NOTE, grid=SIXTEENTH_NOTE)

        self.assertEqual(seq.length, 16)
        self.assertEqual(seq.duration, 2.4)

        seq = Sequence(None, [0, 1, 2, 3], tempo=120, beatValue=QUARTER_NOTE, grid=QUARTER_NOTE)

        self.assertEqual(seq.length, 4)
        self.assertEqual(seq.duration, 2.0)

    def test_exec_order_of_internal_components(self):
        seq = Sequence(None, SIXTEEN_STEPS)
        self.assertEqual(seq.execOrder, [
            seq.phasor, seq.pizza, seq.lookup, seq.lengthener
        ])

    def test_notes_come_through(self):
        """Check outcoming note-ons and note-offs from Sequence for a simple
        pattern of length 4.
        """
        seq = Sequence(None, [1, 2, 3, 4], tempo=120, beatValue=QUARTER_NOTE,
                       grid=QUARTER_NOTE, absNoteLength=1.)

        def set_time(time):
            seq.phasor.currentPhase = TAU / seq.duration * time
            seq.lengthener.clock = lambda: time

        recv = MessageInput()
        seq | recv

        # Single active note
        set_time(0.)
        seq.update()
        note, = recv.receive()

        self.assertTrue(note.on)
        self.assertEqual(note.pitch, 1)

        # Second active note
        set_time(.5)
        seq.update()
        note, = recv.receive()

        self.assertTrue(note.on)
        self.assertEqual(note.pitch, 2)

        # First outdated note and one more active note
        set_time(1.)
        seq.update()
        notes = list(recv.receive())

        self.assertTrue(notes[0].off)
        self.assertEqual(notes[0].pitch, 1)

        self.assertTrue(notes[1].on)
        self.assertEqual(notes[1].pitch, 3)


class TestSequencer(unittest.TestCase):
    def test_correct_number_of_sequences(self):
        sequencer = Sequencer([1, 2, 3, 4])

        self.assertEqual(sequencer.nChannels, 1)

        sequencer = Sequencer([[1, 2, 3, 4]])

        self.assertEqual(sequencer.nChannels, 1)

        sequencer = Sequencer([
            [1, 2, 3, 4],
            [5, 6],
            [7],
        ])

        self.assertEqual(sequencer.nChannels, 3)

    def test_internal_exec_order_with_micro_rhyhtm(self):
        sequencer = Sequencer([
            SIXTEEN_STEPS,
            SIXTEEN_STEPS,
            SIXTEEN_STEPS,
        ])

        self.assertEqual(sequencer.nChannels, 3)
        seq0, seq1, seq2 = sequencer.sequences

        self.assertEqual(sequencer.execOrder, [seq0, seq1, seq2])

        mr = Block(nInputs=1, nOutputs=1)
        sequencer.apply_micro_rhythm(mr, channel=1)

        self.assertEqual(sequencer.execOrder, [seq0, seq1, mr, seq2])

        sequencer.reset_micro_rhythm(channel=1)

        self.assertEqual(sequencer.execOrder, [seq0, seq1, seq2])


if __name__ == '__main__':
    unittest.main()
