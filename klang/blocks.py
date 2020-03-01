"""Audio blocks."""
import collections

import numpy as np
import matplotlib.pyplot as plt

from config import SAMPLING_RATE
from klang.connections import Input, Output
from klang.util import write_wave


def output_neighbors(block):
    """Get output neighbors of block."""
    for output in block.outputs:
        for input_ in output.connections:
            if input_.owner:
                yield input_.owner


def input_neighbors(block):
    """Get input neighbors of block."""
    for input_ in block.inputs:
        for output in input_.connections:
            if output.owner:
                yield output.owner


class Block:

    """Block base class.

    Attributes:
        name (str): Custom name of the owner (if any).
        inputs (list of klang.connections.Input): Input connection.
        outputs (list of klang.connections.Output): Output connection.
    """

    def __init__(self, name='', nInputs=0, nOutputs=0):
        """
        Kwargs:
            nInputs (int): Number of inputs.
            nOutputs (int): Number of outputs.
            name (str): Custom name of the owner.
        """
        self.name = name
        self.inputs = [Input(owner=self) for _ in range(nInputs)]
        self.outputs = [Output(owner=self) for _ in range(nOutputs)]

    @property
    def nInputs(self):
        """Number of inputs."""
        return len(self.inputs)

    @property
    def nOutputs(self):
        """Number of outputs."""
        return len(self.outputs)

    @property
    def input(self):
        """First input."""
        return self.inputs[0]

    @property
    def output(self):
        """First output."""
        return self.outputs[0]

    def update(self):
        """Block's run method.

        Trivia:
            We use 'update' instead of 'run' because of name collision with
            Python thread's run method.
        """
        raise NotImplementedError('Abstract base class')

    def __str__(self):
        if self.name:
            return '%s(%r)' % (self.__class__.__name__, self.name)

        return self.__class__.__name__


class Plotter(Block):
    def __init__(self):
        super().__init__()
        self.buffers = collections.defaultdict(list)

    def register(self, output):
        self.inputs.append(Input(self))
        output.connect(self.inputs[-1])

    def update(self):
        for input in self.inputs:
            self.buffers[input].append(input.get_value())

    def plot(self):
        for input, chunks in self.buffers.items():
            plt.plot(np.concatenate(chunks))


class WavWriter(Block):

    """Write WAV file from input."""

    def __init__(self, filepath, samplingRate=SAMPLING_RATE):
        super().__init__(nInputs=1)
        self.filepath = filepath
        self.samplingRate = samplingRate
        self.buffer = []

    def update(self):
        samples = self.input.get_value()
        self.buffer.append(samples)

    def finalize(self):
        write_wave(np.concatenate(self.buffer), self.filepath, self.samplingRate)
