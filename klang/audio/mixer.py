"""Mono and stereo audio signal mixer."""
from klang.audio.helpers import MONO_SILENCE, STEREO_SILENCE
from klang.audio.panning import CENTER, panning_amplitudes
from klang.block import fetch_output, Block
from klang.connections import Input


__all__ = ['Mixer', 'StereoMixer']


DEFAULT_GAIN = 1.
"""float: Default gain value for new channels."""


class Mixer(Block):

    """Mono mixer with channel gains.

    Attributes:
        gains (list): Gain levels.
    """

    def __init__(self, nInputs=0, gains=None):
        """Kwargs:
            nInputs (int): Number of inputs.
            gains (list): Gain values. nInputs length.
        """
        if gains is None:
            gains = nInputs * [DEFAULT_GAIN]

        assert len(gains) == nInputs
        super().__init__(nInputs=nInputs, nOutputs=1)
        self.gains = gains

    def add_new_channel(self, gain=DEFAULT_GAIN):
        """Add a new input channel to the mixer."""
        # pylint: disable=arguments-differ
        self.inputs.append(Input(owner=self))
        self.gains.append(gain)

    def update(self):
        signalSum = MONO_SILENCE.copy()
        for gain, channel in zip(self.gains, self.inputs):
            signalSum += gain * channel.value

        if self.nInputs > 1:
            signalSum = signalSum / self.nInputs

        self.output.set_value(signalSum)

    def __iadd__(self, other):
        """Inplace add a new block.output or output to the mixer. Return mixer
        for concatenation.
        """
        self.add_new_channel()
        output = fetch_output(other)
        output.connect(self.inputs[-1])
        return self

    __add__ = __iadd__
    __radd__ = __iadd__


class StereoMixer(Mixer):

    """Stereo mixer with panning.

    Attributes:
        pannings (list): Panning levels.
    """

    def __init__(self, nInputs=0, gains=None, pannings=None,
                 mode='constant_power', panLaw=None):
        """Kwargs:
            nInputs (int): Number of inputs.
            gains (list): Gain values. nInputs length.
            pannings (list): Pan levels.
            mode (str): Panning mode.
            panLaw (int): Pan law.
        """
        if pannings is None:
            pannings = nInputs * [CENTER]

        assert len(pannings) == nInputs
        super().__init__(nInputs, gains=gains)
        self.mode = mode
        self.panLaw = panLaw
        self.pannings = pannings

    def add_new_channel(self, gain=DEFAULT_GAIN, panning=CENTER):
        # pylint: disable=arguments-differ
        super().add_new_channel(gain)
        self.pannings.append(panning)

    def update(self):
        signalSum = STEREO_SILENCE.copy()
        for gain, panning, channel in zip(self.gains, self.pannings, self.inputs):
            pan = panning_amplitudes(panning, self.mode, self.panLaw)
            signalSum += gain * pan * channel.get_value()

        if self.nInputs > 1:
            signalSum = signalSum / self.nInputs

        self.output.set_value(signalSum)
