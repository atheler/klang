"""Different syntehsizer voices.

WIP:

Types of voices:
  - Simple envelope voice? Not really needed.
  - OscillatorVoice
  - SampleVoice
  - Voice with filter?
  - Voice with glissando?

Better to combine all cases in one single class?

Envelope + sound generator + filter envelope + pitch curve?

Pitch curve: Via a bend() method?
"""
import copy

from klang.audio.helpers import MONO_SILENCE
from klang.block import Block
from klang.connections import MessageInput


__all__ = ['Voice', 'OscillatorVoice']


class Voice(Block):

    """Base class for single synthesizer voice."""

    def __init__(self, envelope):
        """Args:
            envelope (Envelope): Volume envelope.
        """
        super().__init__(nInputs=0, nOutputs=1)
        self.inputs = [MessageInput(owner=self)]
        self.output.set_value(MONO_SILENCE)
        self.amplitude = 0.
        self.envelope = envelope
        self.currentPitch = 0

    @property
    def active(self):
        """Return True if voice is active (active envelope or pending
        message).
        """
        if self.input.queue:
            return True

        return self.envelope.active

    def process_note(self, note):
        """Process note."""
        if note.on:
            self.amplitude = note.velocity
            self.currentPitch = note.pitch
        else:
            self.currentPitch = 0

        self.envelope.input.push(note)

    def update(self):
        for note in self.input.receive():
            self.process_note(note)

        self.envelope.update()

    def __deepcopy__(self, memo):
        return type(self)(
            envelope=copy.deepcopy(self.envelope)
        )


class OscillatorVoice(Voice):

    """Oscillator + envelope voice."""

    def __init__(self, envelope, oscillator):
        """Args:
            envelope (Envelope): Volume envelope.
            oscillator (Oscillator): Oscillator instance.
        """
        super().__init__(envelope)
        self.oscillator = oscillator

    def process_note(self, note):
        super().process_note(note)
        if note.on:
            self.oscillator.frequency.set_value(note.frequency)

    def update(self):
        super().update()
        self.oscillator.update()
        osc = self.oscillator.output.get_value()
        env = self.envelope.output.get_value()
        signal = self.amplitude * env * osc
        self.output.set_value(signal)

    def __deepcopy__(self, memo):
        return type(self)(
            envelope=copy.deepcopy(self.envelope),
            oscillator=copy.deepcopy(self.oscillator),
        )
