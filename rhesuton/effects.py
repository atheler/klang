"""Audio effects."""
from rhesuton.blocks import Block
from rhesuton.oscillators import Oscillator


def clip(value, lower, upper):
    """Clip value to [lower, upper]."""
    return min(max(value, lower), upper)


class Tremolo(Block):

    """LFO controlled amplitude modulation (AM)."""

    def __init__(self, rate=5., intensity=1.):
        super().__init__(nInputs=3, nOutputs=1)

        _, self.rate, self.intensity = self.inputs
        self.rate.set_value(rate)
        self.intensity.set_value(intensity)

        self.lfo = Oscillator(frequency=rate)

    def update(self):
        # Fetch inputs
        samples = self.input.get_value()
        rate = self.rate.get_value()
        intensity = clip(self.intensity.get_value(), 0., 1.)

        # Update LFO
        self.lfo.frequency.set_value(rate)
        self.lfo.update()

        # Calculate tremolo envelope
        mod = self.lfo.output.get_value()
        env = 1. - intensity * ((1. + mod) / 2.)

        # Set output
        self.output.set_value(env * samples)
