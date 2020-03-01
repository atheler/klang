"""Synthesizer audio blocks."""
import itertools

import numpy as np

from config import BUFFER_SIZE
from klang.audio.envelope import EnvelopeGenerator, AR
from klang.audio.oscillators import Oscillator
from klang.blocks import Block
from klang.connections import MessageInput
from klang.math import clip
from klang.music.tunings import EQUAL_TEMPERAMENT, TEMPERAMENTS
from klang.connections import AlreadyConnectedError


MONO_SILENCE = np.zeros(BUFFER_SIZE)


class Voice(Block):
    def __init__(self, oscillator=None, envelope=None):
        super().__init__(nInputs=0, nOutputs=1)
        self.amplitude = 0.
        self.oscillator = oscillator or Oscillator()
        self.envelope = envelope or EnvelopeGenerator()

    @property
    def frequency(self):
        return self.oscillator.frequency.get_value()

    @property
    def active(self):
        return self.envelope.active

    def process_note(self, frequency, velocity):
        if velocity > 0.:
            self.amplitude = clip(velocity, 0., 1.)
            self.oscillator.frequency.set_value(frequency)
            self.envelope.trigger.set_value(True)
        else:
            self.envelope.trigger.set_value(False)

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
            Voice(envelope=AR(attackTime=.002, releaseTime=.1)) for _  in range(self.MAX_VOICES)
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

        samples = np.zeros(BUFFER_SIZE)
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
