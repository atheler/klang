import unittest

import numpy as np

from klang.audio._envelope import Envelope


class TestEnvelope(unittest.TestCase):
    def test_attributes(self):
        env = Envelope(attack=.1, decay=.2, sustain=.8, release=1., dt=.1)

        self.assertEqual(env.attack, .1)
        self.assertEqual(env.decay, .2)
        self.assertEqual(env.sustain, .8)
        self.assertEqual(env.release, 1.)

        self.assertFalse(env.active)

        env.gate(True)

        self.assertTrue(env.active)

    def test_attack_overwrite(self):
        env = Envelope(attack=1., decay=1., sustain=.5, release=1., dt=.1)
        env.gate(True)
        env.attack = 2.

        self.assertEqual(env.sample(20)[-1], 1.)

    def test_sample(self):
        env = Envelope(attack=.1, decay=.2, sustain=.8, release=1., dt=.1)

        with self.assertRaises(ValueError):
            env.sample(-1)

        np.testing.assert_equal(env.sample(0), [])
        np.testing.assert_equal(env.sample(64), np.zeros(64))


    def test_curve(self):
        env = Envelope(attack=1., decay=1., sustain=.5, release=1., dt=.1)

        np.testing.assert_equal(env.sample(10), np.zeros(10))

        env.gate(True)

        self.assertEqual(env.sample(10)[-1], 1.)
        self.assertEqual(env.sample(10)[-1], .5)
        np.testing.assert_equal(env.sample(10), .5)

        env.gate(False)

        self.assertEqual(env.sample(10)[-1], .0)

        np.testing.assert_equal(env.sample(10), np.zeros(10))


if __name__ == '__main__':
    unittest.main()
