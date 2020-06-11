import unittest

import numpy as np

from klang.audio.helpers import DT, INTERVAL
from klang.audio.oscillators import chirp_phase, sample_phase, Oscillator, Phasor
from klang.config import BUFFER_SIZE, SAMPLING_RATE
from klang.constants import TAU


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


class TestSamplePhase(unittest.TestCase):
    def test_constant_frequency_values(self):
        frequency = 440.
        phase, _ = sample_phase(frequency)

        should = TAU * frequency * DT * np.arange(BUFFER_SIZE)
        should %= TAU

        # Almost due to floating point jitter in time array
        np.testing.assert_almost_equal(phase, should)

    def test_varying_frequency_values(self):
        # Varying frequency
        frequency = np.linspace(440., 880., BUFFER_SIZE)
        phase, _ = sample_phase(frequency)

        should = np.zeros(BUFFER_SIZE)
        should[1:] = TAU * DT * np.cumsum(frequency[:-1])
        should %= TAU

        # Almost due to floating point jitter in time array
        np.testing.assert_almost_equal(phase, should)

    def test_start_phase(self):
        startPhase = 1.234

        # Constant frequency
        phase, _ = sample_phase(440., startPhase)

        np.testing.assert_equal(phase[0], startPhase)

        # Varying frequency
        freqs = np.linspace(440., 880., BUFFER_SIZE)
        phase, _ = sample_phase(freqs, startPhase)

        np.testing.assert_equal(phase[0], startPhase)

    def test_phase_wrap(self):
        freq = 2 / INTERVAL  # Two cycles per BUFFER_SIZE
        should = TAU * freq * DT * np.arange(BUFFER_SIZE)

        phase, _ = sample_phase(freq)
        should = np.linspace(0, 2*TAU, BUFFER_SIZE, endpoint=False) % TAU

        # Almost due to floating point jitter in time array
        np.testing.assert_almost_equal(phase, should)

    def test_new_phase(self):
        freq = 1 / INTERVAL  # One cycle per BUFFER_SIZE. Back to zero.
        _, newPhase = sample_phase(freq)

        self.assertEqual(newPhase , 0.)


class TestPhasor(unittest.TestCase):
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

    def test_around_the_clock(self):
        phasor = Phasor(frequency=.25/INTERVAL)

        self.assertEqual(phasor.sample(), 0. * TAU)
        self.assertEqual(phasor.sample(), 0.25 * TAU)
        self.assertEqual(phasor.sample(), 0.5 * TAU)
        self.assertEqual(phasor.sample(), 0.75 * TAU)
        self.assertEqual(phasor.sample(), 0. * TAU)


class TestOscillator(unittest.TestCase):
    def test_440_hz(self):
        freq = 440.
        osc = Oscillator(frequency=freq)

        t = DT * np.arange(BUFFER_SIZE)
        phase = TAU * freq * t
        should = np.sin(phase)
        osc.update()

        # Almost due to floating point jitter in time array
        np.testing.assert_almost_equal(osc.output.value, should)


if __name__ == '__main__':
    unittest.main()
