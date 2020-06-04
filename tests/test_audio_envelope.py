import unittest
import math

import numpy as np
from scipy.signal import lfilter

from klang.audio.envelope import (
    Envelope,
    calculate_coefficient,
    calculate_transfer_function,
    constant_samples,
    curve_samples,
    full,
    generator_finished,
    time_needed,
    time_needed_until_upper,
)
from klang.config import SAMPLING_RATE, BUFFER_SIZE
from klang.constants import INF



class TestFull(unittest.TestCase):
    def test_caching(self):
        a = full(10, 42.)
        b = full(10, 42.)

        self.assertIs(a, b)

    def test_write_only(self):
        arr = full(10, 42.)
        with self.assertRaises(ValueError):
            arr[0] = 666


class TestCalculateCoefficient(unittest.TestCase):
    def test_edge_cases(self):
        self.assertEqual(calculate_coefficient(-1., 1e-3), INF)
        self.assertEqual(calculate_coefficient(1.234, -1.), 1 / 1.234)


class TestTimeNeededUntilUpper(unittest.TestCase):
    def test_all_the_way(self):
        self.assertEqual(time_needed_until_upper(0., 1.234), 1.234)

    def test_we_are_already_there(self):
        self.assertEqual(time_needed_until_upper(1., 1.234), 0.)


class TestTimeNeeded(unittest.TestCase):
    def test_all_the_way(self):
        self.assertEqual(time_needed(start=0., target=1., duration=1.234), 1.234)


class OnePoleFilter(unittest.TestCase):
    def test_transfer_function(self):
        duration = 1.
        overshoot = 1e-3
        start = .1
        target = .9
        fs = 44100

        rate = duration * fs
        nSamples = int(time_needed(start, target, rate, overshoot))
        tf = calculate_transfer_function(rate, overshoot=overshoot)
        targetArr = full(nSamples, (1. + overshoot) * target)
        samples, _ = lfilter(*tf, targetArr, zi=[start])

        self.assertAlmostEqual(samples[0], start, 3)
        self.assertAlmostEqual(samples[-1], target, 3)


class TestConstantSamples(unittest.TestCase):
    def test_output(self):
        gen = constant_samples(42)
        samples, state = next(gen)

        np.testing.assert_equal(samples, 42)
        self.assertEqual(state, 42)

    def test_output_with_prepend(self):
        prepend = np.arange(10)
        gen = constant_samples(42, prepend)
        samples, state = next(gen)

        np.testing.assert_equal(samples[:10], prepend)
        np.testing.assert_equal(samples[10:], 42)
        self.assertEqual(state, 42)



class TestCurveSamples(unittest.TestCase):
    def test_zero_duration(self):
        gen = curve_samples(.0, 1., duration=0.)
        samples, state = next(gen)

        np.testing.assert_equal(samples, [])
        self.assertEqual(state, 1.)

    def test_zero_duration_with_prepend(self):
        prepend = np.arange(10)
        gen = curve_samples(.0, 1., duration=0., prepend=prepend)
        samples, state = next(gen)

        np.testing.assert_equal(samples, prepend)
        self.assertEqual(state, 1.)

    def test_positive_curve(self):
        start = .1
        target = .9
        duration = 1.
        gen = curve_samples(start, target, duration)
        samples, _ = next(gen)

        self.assertAlmostEqual(samples[0], start, 3)

        while not generator_finished(samples):
            samples, _ = next(gen)

        self.assertAlmostEqual(samples[-1], target, 3)

    def test_negative_curve(self):
        start = .9
        target = .1
        duration = 1.
        gen = curve_samples(start, target, duration)
        samples, _ = next(gen)

        self.assertAlmostEqual(samples[0], start, 3)

        while not generator_finished(samples):
            samples, _ = next(gen)

        self.assertAlmostEqual(samples[-1], target, 3)

    def test_sentinel_with_no_remainder(self):
        duration = BUFFER_SIZE / SAMPLING_RATE  # Exactly one full buffer
        target = 1.
        gen = curve_samples(0., target, duration=BUFFER_SIZE / SAMPLING_RATE)
        samples, _ = next(gen)

        self.assertEqual(samples.size, BUFFER_SIZE)

        samples, state = next(gen)

        self.assertEqual(samples.size, 0)  # Sentinel
        self.assertEqual(state, target)

        with self.assertRaises(StopIteration):
            next(gen)


def number_of_blocks(duration):
    return int(math.ceil(duration * SAMPLING_RATE / BUFFER_SIZE))


class TestEnvelope(unittest.TestCase):
    def test_curve(self):
        env = Envelope(.2, .2, .8, 1.)

        np.testing.assert_equal(env.sample(), 0.)

        self.assertFalse(env.active)

        env.gate(True)

        self.assertTrue(env.active)

        for _ in range(number_of_blocks(env.attack + env.decay)):
            samples = env.sample()

        np.testing.assert_equal(samples, env.sustain)

        self.assertTrue(env.active)

        env.gate(False)

        self.assertTrue(env.active)

        samples = env.sample()

        self.assertAlmostEqual(samples[0], env.sustain, 6)

        for _ in range(number_of_blocks(env.release)):
            samples = env.sample()

        np.testing.assert_equal(samples, 0.)
        self.assertFalse(env.active)

    def test_no_attack(self):
        env = Envelope(.0, .2, .8, 1.)
        env.gate(True)

        samples = env.sample()

        self.assertAlmostEqual(samples[0], 1., 2)

    def test_retrigger(self):
        # TODO: How to test?
        pass

    def test_loop(self):
        # TODO: How to test?
        pass


if __name__ == '__main__':
    unittest.main()
