import unittest

import numpy as np

from klang.config import BUFFER_SIZE, SAMPLING_RATE
from klang.audio.helpers import DT, INTERVAL
from klang.audio.oscillators import chirp_phase, Oscillator, Phasor
from klang.constants import TAU


class TestPhaseor(unittest.TestCase):
    def test_phasor(self):
        freq = .5
        phasor = Phasor(frequency=freq)

        self.assertEqual(phasor.currentPhase, 0.)

        phasor.update()

        self.assertEqual(phasor.currentPhase, TAU*freq*INTERVAL)

    def test_phase_wrap(self):
        freq = 10.
        phasor = Phasor(frequency=freq)
        atLeastOneCycle = int((SAMPLING_RATE / freq) // BUFFER_SIZE) + 1
        for _ in range(atLeastOneCycle):
            phasor.update()

        self.assertAlmostEqual(phasor.currentPhase, atLeastOneCycle*TAU*freq*INTERVAL % TAU)


class TestOscillator(unittest.TestCase):
    def test_440_hz(self):
        freq = 440.
        osc = Oscillator(frequency=freq)

        t = DT * np.arange(BUFFER_SIZE)
        ref = np.sin(TAU * freq * t)
        osc.update()

        np.testing.assert_equal(osc.output.value, ref)


class TestChirpPhase(unittest.TestCase):
    def test_constant_frequency_same_args(self):
        tEnd = 1.
        freqStart = 1.234
        t, dt = np.linspace(0, tEnd, 10, endpoint=False, retstep=True)
        phase = chirp_phase(t, freqStart, tEnd, freqEnd=freqStart)
        omega = np.diff(phase) / dt

        np.testing.assert_almost_equal(omega / TAU, freqStart)
    
    def test_constant_frequency_region(self):
        freqStart = 1.234
        t, dt = np.linspace(1., 2., 10, endpoint=False, retstep=True)
        phase = chirp_phase(t, freqStart, tEnd=1., freqEnd=freqStart)
        omega = np.diff(phase) / dt

        np.testing.assert_almost_equal(omega / TAU, freqStart)

    def test_chirp(self):
        tEnd = 1.
        t, dt = np.linspace(0, 1., 128, endpoint=False, retstep=True)
        freqStart = 2.
        phase = chirp_phase(t, freqStart, tEnd, freqEnd=3., method='linear')
        omega = np.diff(phase) / dt
        alpha = np.diff(omega) / dt

        np.testing.assert_allclose(alpha, TAU)

    def test_mixture_between_chirp_and_constant_frequency(self):
        t, dt = np.linspace(0, 1., 128, retstep=True)
        phase = chirp_phase(t, freqStart=1., tEnd=1., freqEnd=2.)
        alpha = np.diff(phase, n=2) / dt**2

        np.testing.assert_allclose(alpha, TAU)

        t, dt = np.linspace(1., 10., 128, retstep=True)
        phase = chirp_phase(t, freqStart=1., tEnd=1., freqEnd=2.)
        alpha = np.diff(phase, n=2) / dt**2

        np.testing.assert_allclose(alpha, 0., atol=1e-10)

    def test_phase_continuation(self):
        t, dt = np.linspace(0, 2., 128, retstep=True)
        phase = chirp_phase(t, freqStart=1., tEnd=1., freqEnd=2.)
        delta = np.diff(phase)

        np.testing.assert_array_less(delta, .2)


if __name__ == '__main__':
    unittest.main()
