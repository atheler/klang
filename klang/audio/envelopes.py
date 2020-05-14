"""Envelope generator blocks."""
from config import BUFFER_SIZE
from klang.audio import DT
from klang.audio._envelope import Envelope as _CEnvelope
from klang.block import Block
from klang.connections import MessageInput


class EnvelopeBase(Block):
    def __init__(self, attack, decay, sustain, release, overshoot, retrigger=False, loop=False):
        super().__init__(nOutputs=1)
        self.inputs = self.trigger, = [MessageInput(owner=self)]
        self._envelope = _CEnvelope(
            attack=attack,
            decay=decay,
            sustain=sustain,
            release=release,
            dt=DT,
            overshoot=overshoot,
            retrigger=retrigger,
            loop=loop,
        )

    @property
    def current_level(self):
        """Get current / latest envelope level."""
        return self.output.get_value()[-1]

    @property
    def active(self):
        """Check if envelope is active."""
        #TODO: Get active state from envelope
        if self.triggered:
            return True
        
        return self.current_level > 0.

    def update(self):
        for msg in self.input.receive():
            self._envelope.trigger(bool(msg))

        samples = self._env.sample(BUFFER_SIZE)
        self.output.set_value(samples)


class ADSR(EnvelopeBase):
    #TODO: Make me!
    pass


class AR(EnvelopeBase):
    #TODO: Make me!
    pass


class D(EnvelopeBase):
    #TODO: Make me!
    pass


class R(EnvelopeBase):
    #TODO: Make me!
    pass
