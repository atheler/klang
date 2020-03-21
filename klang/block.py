"""Audio blocks."""
import abc

from klang.connections import Input, Output


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

    @abc.abstractmethod
    def update(self):
        """Block's run method.

        Trivia:
            We use 'update' instead of 'run' because of name collision with
            Python thread's run method.
        """
        return

    def __str__(self):
        if self.name:
            return '%s(%r)' % (self.__class__.__name__, self.name)

        return self.__class__.__name__
