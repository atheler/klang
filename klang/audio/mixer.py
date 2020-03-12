"""Mixer"""
import numpy as np

from klang.audio import MONO_SILENCE, STEREO_SILENCE
from klang.blocks import Block
from klang.constants import MONO, STEREO
from klang.math import clip


LEFT = -1.
"""int: Maximum left panning value."""

RIGHT = 1.
"""int: Maximum right panning value."""


class Mixer(Block):

    """Mixer block.

    TODO:
      - Levels
      - Panning
      - Surround?
    """

    def __init__(self, nInputs=2, nOutputs=MONO):
        assert nOutputs in {MONO, STEREO}
        super().__init__(nInputs=nInputs, nOutputs=nOutputs)
        self.gains = np.ones(nInputs)

    def set_gain(self, channel, gain):
        self.gains[channel] = clip(gain, 0., 1.)

    def update(self):
        signalSum = MONO_SILENCE.copy()
        for gain, channel in zip(self.gains, self.inputs):
            signalSum += gain * channel.get_value()

        if self.nInputs > 1:
            signalSum /= self.nInputs

        for output in self.outputs:
            output.set_value(signalSum)


class StereoMixer(Mixer):
    def __init__(self, nInputs=2):
        raise NotImplementedError
        super().__init__(nInputs, nOutputs=STEREO)
        self.panning = np.zeros(nInputs)

    def set_panning(self, channel, panning):
        self.panning[channel] = clip(panning, LEFT, RIGHT)

    def update(self):
        # TODO(atheler): Make me!
        signalSum = STEREO_SILENCE.copy()
        for gain, channel in zip(self.gains, self.inputs):
            signalSum += gain * channel.get_value()

        if self.nInputs > 1:
            signalSum /= self.nInputs

        for output in self.outputs:
            output.set_value(signalSum)
