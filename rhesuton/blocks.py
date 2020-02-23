import collections

import numpy as np
import matplotlib.pyplot as plt

from rhesuton.errors import RhesutonError


class NotConnectedError(RhesutonError):

    """Connectable is not connected."""

    pass


class InputAlreadyConnectedError(RhesutonError):

    """Connectable already connected."""

    pass


class Connectable:

    """Base class."""

    def __init__(self, owner, value=0.):
        self.owner = owner
        self.value = value
        self.connections = set()

    def connect(self, other):
        """Make a connection to another connectable."""
        self.connections.add(other)
        other.connections.add(self)

    def disconnect(self, other):
        """Disconnect from another connectable."""
        self.connections.remove(other)
        other.connections.remove(self)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    @property
    def connected(self):
        """Is connected?"""
        return bool(self.connections)

    def __str__(self):
        return '%s(connected: %s)' % (self.__class__.__name__, self.connected)


class Input(Connectable):

    """Input slot.

    Can be connected to only one output.
    """

    def connect(self, output):
        assert isinstance(output, Output)
        if self.connected:
            msg = 'Only one connection possible for Input owner!'
            raise InputAlreadyConnectedError(msg)

        super().connect(output)

    def get_value(self):
        if not self.connected:
            return self.value

        output, = self.connections
        return output.value


class Output(Connectable):

    """Output slot.

    Holds the value. Can be connected to multiple inputs.
    """

    def connect(self, input):
        assert isinstance(input, Input)
        super().connect(input)


class Block:

    """Block base class.

    Attributes:
        name (str): Custom name of the owner (if any).
        inputs (list of Input): Input connection.
        outputs (list of Output): Output connection.
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
            return '%s(%s)' % (self.__class__.__name__, self.name)

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
