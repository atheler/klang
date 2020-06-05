"""Envelope generator blocks."""
from klang.config import BUFFER_SIZE
from klang.audio.helpers import DT
try:
    # C Envelope
    from klang.audio._envelope import Envelope
except ImportError:
    # Pure Python fallback
    from klang.audio.envelope import Envelope
from klang.audio.envelope import DEFAULT_OVERSHOOT
from klang.block import Block
from klang.connections import MessageInput


__all__ = ['ADSR', 'AR', 'D', 'R']


class EnvelopeBase(Block, Envelope):
    def __init__(self, attack, decay, sustain, release,
                 overshoot=DEFAULT_OVERSHOOT, retrigger=False, loop=False):
        super().__init__(nOutputs=1)
        self.inputs = self.trigger, = [MessageInput(owner=self)]
        Envelope.__init__(
            self,
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

    def update(self):
        for note in self.input.receive():
            self.gate(note.on)

        samples = self.sample(BUFFER_SIZE)
        self.output.set_value(samples)

    def __str__(self):
        infos = []
        for name in ['attack', 'decay', 'sustain', 'release', 'retrigger', 'loop']:
            val = getattr(self, name)
            if val:
                infos.append('%s=%s' % (name, val))

        return '%s(%s)' % (type(self).__name__, ', '.join(infos))

    def __deepcopy__(self, memo):
        args = (self.attack, self.decay, self.sustain, self.release)
        kwargs = {'overshoot': self.overshoot, 'retrigger': self.retrigger, 'loop': self.loop}
        return type(self)(*args, **kwargs)


class ADSR(EnvelopeBase):

    """Attack-decay-sustain-release envelope."""

    def __init__(self, attack=.1, decay=.2, sustain=.8, release=1., *args, **kwargs):
        super().__init__(attack, decay, sustain, release, *args, **kwargs)


class AR(EnvelopeBase):

    """Attack-release only envelope.

    Sustain is fixed to 1.
    """

    def __init__(self, attack=.1, release=1., *args, **kwargs):
        super().__init__(attack, decay=0., sustain=1., release=release, *args, **kwargs)

    def __deepcopy__(self, memo):
        args = (self.attack, self.release)
        kwargs = {'overshoot': self.overshoot, 'retrigger': self.retrigger, 'loop': self.loop}
        return type(self)(*args, **kwargs)


class D(EnvelopeBase):

    """Decay only envelope.

    No sustain / release phase.

    TODO: How to link decay with sustain for continuation?
    """

    def __init__(self, decay=1., *args, **kwargs):
        super().__init__(attack=0., decay=decay, sustain=0., release=decay, *args, **kwargs)

    def __deepcopy__(self, memo):
        args = (self.decay,)
        kwargs = {'overshoot': self.overshoot, 'retrigger': self.retrigger, 'loop': self.loop}
        return type(self)(*args, **kwargs)


class R(EnvelopeBase):

    """Release only envelope."""

    def __init__(self, release=1., *args, **kwargs):
        super().__init__(attack=0., decay=0., sustain=1., release=release, *args, **kwargs)

    def __deepcopy__(self, memo):
        args = (self.release,)
        kwargs = {'overshoot': self.overshoot, 'retrigger': self.retrigger, 'loop': self.loop}
        return type(self)(*args, **kwargs)
