import unittest

import numpy as np

from klang.audio.envelopes import ADSR
from klang.audio.helpers import MONO_SILENCE
from klang.audio.oscillators import Oscillator, PwmOscillator
from klang.audio.voices import Voice
from klang.messages import Note


def create_voice():
    """Get an initialized Voice instance."""
    osc = Oscillator()
    env = ADSR(0., 0., 1., 0.)
    return Voice(osc, env)


class TestVoice(unittest.TestCase):
    def test_active(self):
        voice = create_voice()

        self.assertFalse(voice.active)

        noteOn = Note(60, velocity=1.)
        voice.input.push(noteOn)

        self.assertTrue(voice.active)  # <- Input message

        voice.update()

        self.assertTrue(voice.active)  # <- Envelope

        noteOff = Note(60, velocity=0.)
        voice.input.push(noteOff)
        voice.update()

        self.assertFalse(voice.active)  # <- No message, non-active envelope

    def test_amplitude_on_note_off(self):
        voice = create_voice()

        self.assertEqual(voice.amplitude, 0)

        noteOn = Note(60, velocity=.5)
        voice.input.push(noteOn)
        voice.update()

        self.assertEqual(voice.amplitude, .5)

        noteOff = Note(60, velocity=.0)
        voice.input.push(noteOff)
        voice.update()

        self.assertEqual(voice.amplitude, .5)

    def test_audio_samples(self):
        voice = create_voice()
        voice.update()

        np.testing.assert_equal(voice.output.value, MONO_SILENCE)

        noteOn = Note(60, velocity=.5)
        voice.input.push(noteOn)
        voice.update()

        self.assertTrue(np.all(voice.output.value != 0.))

    def test_external_block_in_exec_order(self):
        """Check that externally connected LFO block gets executed."""
        osc = PwmOscillator()
        lfo = Oscillator()
        lfo.output.connect(osc.dutyCycle)
        env = ADSR()
        voice = Voice(osc, env)

        self.assertEqual(voice.execOrder, [env, lfo, osc])


if __name__ == '__main__':
    unittest.main()
