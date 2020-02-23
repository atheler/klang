import collections

import matplotlib.pyplot as plt

from rhesuton.errors import RhesutonError


class NotConnected(RhesutonError):
    pass


class AlreadyConnected(RhesutonError):
    pass


class Connectable:

    """Base class."""

    def __init__(self):
        self.connections = set()

    def connect(self, other):
        self.connections.add(other)
        other.connections.add(self)

    """
    def disconnect(self, other):
        self.connections.remove(other)
        other.connections.remove(self)
    """

    @property
    def connected(self):
        return bool(self.connections)

    def __str__(self):
        return '%s(connected: %s)' % (self.__class__.__name__, self.connected)


class Input(Connectable):

    """Input slot.

    Can be connected to only one output.
    """

    def __init__(self, value=0.):
        """Kwargs:
            value (?): Initial placeholder value.
        """
        super().__init__()
        self._value = value

    def connect(self, output):
        assert isinstance(output, Output)
        if self.connected:
            msg = 'Only one connection possible for Input block!'
            raise AlreadyConnected(msg)

        super().connect(output)

    def set_value(self, value):
        self._value = value

    def get_value(self):
        if not self.connected:
            return self._value

        output, = self.connections
        return output.get_value()


class Output(Connectable):

    """Output slot.

    Holds the value. Can be connected to multiple inputs.
    """

    def __init__(self, value=0.):
        """Kwargs:
            value (?): Initial value.
        """
        super().__init__()
        self._value = value

    def connect(self, input):
        assert isinstance(input, Input)
        super().connect(input)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value


class Block(object):

    """Block base class.

    Attributes:
        name (str): Custom name of the block (if any).
        inputs (list of Input): Input connection.
        outputs (list of Output): Output connection.
    """

    def __init__(self, name='', nInputs=0, nOutputs=0):
        """
        Kwargs:
            nInputs (int): Number of inputs.
            nOutputs (int): Number of outputs.
            name (str): Custom name of the block.
        """
        self.name = name
        self.inputs = [Input() for _ in range(nInputs)]
        self.outputs = [Output() for _ in range(nOutputs)]

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
        self.inputs.append(Input())
        output.connect.self.inputs[-1]

    def update(self):
        for input in self.inputs:
            value = input.get_value()
            self.buffers[input].append(value)

    def plot(self):
        for input, chunks in self.buffers.items():
            plt.plot(np.concatenate(chunks))
