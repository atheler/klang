import numpy as np

from config import BUFFER_SIZE
from klang.blocks import Block
from klang.constants import MONO, STEREO


class Mixer(Block):

    """Mixer block.

    TODO:
      - Levels
      - Panning
      - Surround?
      - Digital summing? Soft distortion with tanh?

    Resources:
      - https://dsp.stackexchange.com/questions/3581/algorithms-to-mix-audio-signals-without-clipping)
    """

    def __init__(self, nInputs=2, nOutputs=MONO):
        assert nOutputs in {MONO, STEREO}
        super().__init__(nInputs=nInputs, nOutputs=nOutputs)

    def update(self):
        signalSum = np.zeros(BUFFER_SIZE)
        for channel in self.inputs:
            signalSum += channel.get_value()

        if self.nInputs > 1:
            signalSum /= self.nInputs

        for output in self.outputs:
            output.set_value(signalSum)
