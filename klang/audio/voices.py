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

from klang.composite import Composite
from klang.connections import MessageInput
from klang.execution import execute


__all__ = ['Voice']


class Voice(Composite):

    """Single synthesizer voice."""

    def __init__(self, oscillator, envelope):
        """Args:
            oscillator (Oscillator): Oscillator-like block. Frequency input -> value output.
            envelope (Envelope): Envelope generator.
        """
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(owner=self)]
        self.oscillator = oscillator
        self.envelope = envelope
        self.amplitude = 0.
        self.currentPitch = 0
        self.update_internal_exec_order(self.oscillator, self.envelope)

    @property
    def active(self):
        """Return True if voice is active (active envelope or pending
        message).
        """
        if self.input.queue:
            return True

        return self.envelope.active

    def process_incoming_notes(self):
        """Process all incoming notes."""
        for note in self.input.receive():
            self.envelope.gate(note.on)
            if note.on:
                self.amplitude = note.velocity
                self.oscillator.frequency.set_value(note.frequency)
                self.currentPitch = note.pitch
            else:
                self.currentPitch = 0

    def update(self):
        self.process_incoming_notes()
        execute(self.execOrder)

        # Assemble output samples
        env = self.oscillator.output.value
        osc = self.envelope.output.value
        signal = self.amplitude * env * osc
        self.output.set_value(signal)

    def __deepcopy__(self, memo):
        return type(self)(
            oscillator=copy.deepcopy(self.oscillator),
            envelope=copy.deepcopy(self.envelope),
        )
