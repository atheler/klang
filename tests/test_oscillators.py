import unittest

import numpy as np

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.audio import DT
from klang.audio.oscillators import Phasor, Oscillator, Lfo
from klang.constants import TAU


DELTA = DT * BUFFER_SIZE


class TestPhaseor(unittest.TestCase):
    def test_phasor(self):
        freq = .5
        phasor = Phasor(frequency=freq)

        self.assertEqual(phasor.currentPhase, 0.)

        phasor.update()

        self.assertEqual(phasor.currentPhase, TAU*freq*DELTA)

    def test_phase_wrap(self):
        freq = 10.
        phasor = Phasor(frequency=freq)
        atLeastOneCycle = int((SAMPLING_RATE / freq) // BUFFER_SIZE) + 1
        for _ in range(atLeastOneCycle):
            phasor.update()

        self.assertAlmostEqual(phasor.currentPhase, atLeastOneCycle*TAU*freq*DELTA % TAU)


class TestOscillator(unittest.TestCase):
    def test_400_hz(self):
        freq = 440.
        osc = Oscillator(frequency=freq)

        t = DT * np.arange(BUFFER_SIZE)
        ref = np.sin(TAU * freq * t)
        osc.update()

        np.testing.assert_equal(osc.output.value, ref)


class TestLfo(unittest.TestCase):
    def test_400_hz(self):
        freq = 440.
        lfo = Lfo(frequency=freq)

        t = DT * np.arange(BUFFER_SIZE)
        ref = np.sin(TAU * freq * t - .25 * TAU)
        ref = (ref + 1.) / 2.
        lfo.update()

        np.testing.assert_equal(lfo.output.value, ref)


if __name__ == '__main__':
    unittest.main()
