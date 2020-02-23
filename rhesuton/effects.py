"""Audio effects."""
from rhesuton.blocks import Block
from rhesuton.math import clip
from rhesuton.oscillators import Oscillator
from rhesuton.constants import TAU


class Tremolo(Block):

    """LFO controlled amplitude modulation (AM)."""

    def __init__(self, rate=5., intensity=1.):
        super().__init__(nInputs=3, nOutputs=1)
        _, self.rate, self.intensity = self.inputs
        self.rate.set_value(rate)
        self.intensity.set_value(intensity)

        self.lfo = Oscillator(frequency=rate)
        self.lfo.currentPhase = TAU / 4.  # Start from zero

    def update(self):
        # Fetch inputs
        samples = self.input.get_value()
        rate = self.rate.get_value()
        intensity = self.intensity.get_value()

        # Update LFO
        self.lfo.frequency.set_value(rate)
        self.lfo.update()

        # Calculate tremolo envelope. [-1, +1] mod signal gets mapped onto
        # [0., 1.] and then used to subtract from unity. Depending on intensity
        # level.
        mod = self.lfo.output.get_value()
        env = 1. - clip(intensity, 0., 1.) * ((1. + mod) / 2.)

        # Set output
        self.output.value = env * samples
