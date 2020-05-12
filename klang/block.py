"""Audio blocks."""
from klang.connections import OutputBase, InputBase, Output, Input


def output_neighbors(block):
    """Get output neighbors of block."""
    for output in block.outputs:
        for input_ in output.outgoingConnections:
            if input_.owner:
                yield input_.owner


def input_neighbors(block):
    """Get input neighbors of block."""
    for input_ in block.inputs:
        if input_.connected:
            output = input_.incomingConnection
            if output.owner:
                yield output.owner


def fetch_input(other):
    """Fetch input from other."""
    if isinstance(other, Block):
        return other.input

    return other


def fetch_output(other):
    """Fetch output from other."""
    if isinstance(other, Block):
        return other.output

    return other


def pipe_operator(left, right):
    """Pipe blocks or connections together. pipe_operator(a, b) is the same as
    a.output.connect(b). Left to right. Return rightmost block for
    concatenation.

    Args:
        left (Block or OutputBase): Left operand.
        right (Block or InputBase): Right operand.

    Returns:
        Block: Owner of incoming connection.
    """
    output = fetch_output(left)
    input_ = fetch_input(right)
    if not isinstance(output, OutputBase)\
        or not isinstance(input_, InputBase):
        raise TypeError('Can not pipe from %s to %s' % (left, right))

    output.connect(input_)
    return input_.owner


def mix_operator(left, right):
    """Mix two audio blocks (or outputs) together with a new Mixer instance.
    Returns this mixer for concatenation. Only audio outputs can be mixed!

    Args:
        left (Block or Output or Mixer): Left operand.
        right (Block or Output): Right operand.

    Returns:
        Mixer: Mixer instance.
    """
    leftOutput = fetch_output(left)
    rightOutput = fetch_output(right)
    if not isinstance(leftOutput, Output)\
        or not isinstance(rightOutput, Output):
        raise TypeError('Can not mix %s with %s' % (left, right))

    from klang.audio.mixer import Mixer  # Circular import for comforts
    mixer = Mixer(nInputs=0)
    mixer += left
    mixer += right
    return mixer


class Block:

    """Block base class.

    Child classes have to override the update() method. This will be called once
    per audio buffer.

    Attributes:
        inputs (list of klang.connections.Input): Input connection.
        outputs (list of klang.connections.Output): Output connection.
        name (str): Custom name of the owner (if any).
    """

    def __init__(self, nInputs=0, nOutputs=0, name=''):
        """
        Kwargs:
            nInputs (int): Number of inputs.
            nOutputs (int): Number of outputs.
            name (str): Custom name of the owner.
        """
        self.inputs = [Input(owner=self) for _ in range(nInputs)]
        self.outputs = [Output(owner=self) for _ in range(nOutputs)]
        self.name = name

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
        if not self.inputs:
            raise AttributeError('Block has no inputs!')

        return self.inputs[0]

    @property
    def output(self):
        """First output."""
        if not self.outputs:
            raise AttributeError('Block has no outputs!')

        return self.outputs[0]

    def update(self):
        """Block's update / run / tick method."""
        pass

    def __str__(self):
        infos = []
        if self.name:
            infos.append('name: %r' % self.name)

        if self.nInputs > 0:
            infos.append('%d inputs' % self.nInputs)

        if self.nOutputs > 0:
            infos.append('%d outputs' % self.nOutputs)

        return '%s(%s)' % (type(self).__name__, ', '.join(infos))

    __or__ = pipe_operator

    def __ror__(self, output):
        """Connect output with block."""
        # Reverse operands. Maintain order.
        return pipe_operator(output, self)

    __add__ = mix_operator

    def __radd__(self, output):
        """Mix output and block."""
        # Reverse operands. Maintain order.
        return mix_operator(output, self)
