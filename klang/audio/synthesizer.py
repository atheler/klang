"""Synthesizer audio blocks."""
import itertools

import numpy as np

from config import BUFFER_SIZE
from klang.audio import MONO_SILENCE, DT
from klang.audio.envelope import sample_exponential_decay, EnvelopeGenerator, AR, ExpDecay
from klang.audio.oscillators import Oscillator, sample_wave
from klang.blocks import Block
from klang.connections import MessageInput
from klang.math import clip
from klang.music.tunings import EQUAL_TEMPERAMENT, TEMPERAMENTS
from klang.connections import AlreadyConnectedError


class Voice(Block):
    def __init__(self, envelope):
        super().__init__(nOutputs=1)
        self.amplitude = 0.
        self.envelope = envelope

    @property
    def active(self):
        return self.envelope.active

    def process_note(self, velocity):
        self.amplitude = clip(velocity, 0., 1.)
        self.envelope.trigger.set_value(velocity > 0.)


class OscillatorVoice(Voice):
    def __init__(self, oscillator=None, envelope=None):
        super().__init__(envelope or EnvelopeGenerator())
        self.oscillator = oscillator or Oscillator()

    @property
    def frequency(self):
        return self.oscillator.frequency.get_value()

    def process_note(self, frequency, velocity):
        super().process_note(velocity)
        if velocity > 0.:
            self.oscillator.frequency.set_value(frequency)

    def update(self):
        self.oscillator.update()
        osc = self.oscillator.output.get_value()

        self.envelope.update()
        env = self.envelope.output.get_value()

        signal = self.amplitude * env * osc
        self.output.set_value(signal)


class Synthesizer(Block):

    """Simple polyphonic synthesizer."""

    MAX_VOICES = 24

    def __init__(self, temperament=EQUAL_TEMPERAMENT):
        super().__init__(nInputs=0, nOutputs=1)
        self.temperament = temperament

        self.inputs = [MessageInput(self)]
        self.output.set_value(MONO_SILENCE)

        self.voices = [
            OscillatorVoice(envelope=AR(attackTime=0.02, releaseTime=.1)) for _  in range(self.MAX_VOICES)
        ]
        self.freeVoice = itertools.cycle(self.voices)

    def play_notes(self, *notes):
        """Play notes."""
        if self.input.connected:
            fmt = 'Synthesizer input is already connected with %s!'
            other, = self.input.connections
            msg = fmt % other.owner
            raise AlreadyConnectedError(msg)

        queue = self.input.value()
        queue.extend(notes)

    def process_note(self, note):
        """Process note."""
        freq = self.temperament.pitch_2_frequency(note.pitch)
        if note.velocity > 0:
            #print('Play new note')
            voice = next(self.freeVoice)
            voice.process_note(freq, note.velocity)
        else:
            #print('Kill old note')
            for voice in self.voices:
                if voice.frequency == freq:
                    voice.process_note(freq, note.velocity)

    def update(self):
        for note in self.input.receive():
            self.process_note(note)

        samples = MONO_SILENCE.copy()
        for voice in self.voices:
            if not voice.active:
                continue

            voice.update()
            samples += voice.output.get_value()

        samples /= self.MAX_VOICES
        self.output.set_value(samples)


_temperaments = list(TEMPERAMENTS.values())


class TemperamentSynthesizer(Synthesizer):
    def __init__(self):
        super().__init__()
        self.inputs.append(MessageInput(self))

    def update(self):
        for key in self.inputs[1].receive():
            try:
                char = key.char
                idx = int(char)
            except (AttributeError, ValueError):
                continue

            if 0 <= idx < len(_temperaments):
                self.temperament = _temperaments[idx]
                print('Switched to %s' % self.temperament)

        super().update()


class HiHat(Block):

    """White noise / exponential decay hi hat synthesizer."""

    def __init__(self, decay=.05, loopedNoise=False):
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(self)]
        if loopedNoise:
            noise = 2 * np.random.random(BUFFER_SIZE) - 1.
            self.noise_generator = lambda: noise
        else:
            self.noise_generator = lambda: 2 * np.random.random(BUFFER_SIZE) - 1.

        self.envelope = ExpDecay(decay)

    def update(self):
        triggered = False
        for note in self.input.receive():
            if note.pitch > 0 and note.velocity > 0:
                triggered = True

        self.envelope.trigger.set_value(triggered)
        self.envelope.update()
        env = self.envelope.output.get_value()
        noise = self.noise_generator()
        self.output.set_value(env * noise)


def sample_pitch_decay(frequency, decay, intensity, t0=0.):
    """Sample decaying pitch curve."""
    env, t1 = sample_exponential_decay(decay, t0)
    pitch = frequency * (1. + intensity * env)
    return pitch, t1


class Kick(Block):
    def __init__(self, frequency=40., decay=.8, intensity=2, pitchDecay=.3):
        super().__init__(nInputs=0, nOutputs=1)
        self.frequency = frequency
        self.decay = decay
        self.intensity = intensity
        self.pitchDecay = pitchDecay

        self.inputs = [MessageInput(self)]
        self.currentTime = 0.
        self.currentPhase = 0.

    def update(self):
        triggered = False
        for note in self.input.receive():
            if note.pitch > 0 and note.velocity > 0:
                triggered = True

        if triggered:
            self.currentTime = 0.
            self.currentPhase = 0.

        frequency, _ = sample_pitch_decay(self.frequency, self.pitchDecay, self.intensity, self.currentTime)
        env, self.currentTime = sample_exponential_decay(self.decay, self.currentTime)
        signal, self.currentPhase = sample_wave(None, frequency, startPhase=self.currentPhase)
        self.output.set_value(env * signal)
