"""Mixer"""
from klang.audio import MONO_SILENCE, STEREO_SILENCE
from klang.audio.panning import CENTER, panning_amplitudes
from klang.block import Block
from klang.constants import MONO, STEREO
from klang.math import clip


class Mixer(Block):

    """Mono mixer with channel gains."""

    def __init__(self, nInputs=2, nOutputs=MONO, gains=None):
        if gains is None:
            gains = nInputs * [1.]

        assert nOutputs in {MONO, STEREO}
        assert len(gains) == nInputs
        super().__init__(nInputs=nInputs, nOutputs=nOutputs)
        self.gains = gains

    def set_gain(self, channel, gain):
        """Set gain level for a given channel."""
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

    """Stereo mixer with panning."""

    def __init__(self, nInputs=2, gains=None, mode='constant_power', panLaw=None):
        super().__init__(nInputs, nOutputs=STEREO, gains=gains)
        self.mode = mode
        self.panLaw = panLaw
        self.panning = [
            panning_amplitudes(CENTER, self.mode, self.panLaw)
            for _ in range(nInputs)
        ]

    def set_pan_level(self, channel, panLevel):
        """Set pan level for a channel."""
        self.panning[channel] = panning_amplitudes(panLevel, self.mode, self.panLaw)

    def update(self):
        signalSum = STEREO_SILENCE.copy()
        for gain, panning, channel in zip(self.gains, self.panning, self.inputs):
            signalSum += gain * panning * channel.get_value()

        if self.nInputs > 1:
            signalSum /= self.nInputs

        for output in self.outputs:
            output.set_value(signalSum)
