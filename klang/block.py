"""Klang blocks.

Blocks represent the central unit in Klang. Each block can have multiple inputs
and outputs with which it is connected to other blocks. Blocks use mostly value
based connections for audio and control signals. But message based ones can be
applied See the following example:

    >>> class Foo(Block):
    ... 
    ...     '''Block with a message input and a value output'''
    ... 
    ...     def __init__(self):
    ...         super().__init__(nOutputs=1)
    ...         self.inputs = [MessageInput(owner=self)]

Besides the Block base class the pipe_operator() and mix_operator() are also
defined here (for operation overloading).
"""
import functools

from klang.connections import OutputBase, InputBase, Output, Input


def input_connections(block):
    """Iterate over all incoming connections.

    Args:
        block (Block): Block to inspect.

    Yields:
        tuple: Src -> block input connections.
    """
    for input_ in block.inputs:
        if input_.connected:
            src = input_.incomingConnection
            if src.owner is not block:
                yield src, input_


def output_connections(block):
    """Iterate over all outgoing connections.

    Args:
        block (Block): Block to inspect.

    Yields:
        tuple: Block output -> dst.
    """
    for output in block.outputs:
        for dst in output.outgoingConnections:
            if dst.owner is not block:
                yield output, dst


def collect_connections(block):
    """Get all in- and outgoing connections of a block ((output, input) tuples).
    Exclude loop-around connections (block connected to itself).

    Args:
        block (Block): Block to inspect.

    Yields:
        tuple: Output -> input connections
    """
    yield from input_connections(block)
    yield from output_connections(block)


def input_neighbors(block):
    """Get input neighbors of block.

    Args:
        block (Block): Block to inspect

    Yields:
        Block: Input neighbors / source owners.
    """
    for src, _ in input_connections(block):
        if src.owner:
            yield src.owner


def output_neighbors(block):
    """Get output neighbors of block.

    Args:
        block (Block): Block to inspect

    Yields:
        Block: Output neighbors / destination owner.
    """
    for _, dst in output_connections(block):
        if dst.owner:
            yield dst.owner


def fetch_input(blockOrInput):
    """Fetch primary input."""
    if isinstance(blockOrInput, Block):
        return blockOrInput.input

    return blockOrInput


def fetch_output(blockOrOutput):
    """Fetch primary output."""
    if isinstance(blockOrOutput, Block):
        return blockOrOutput.output

    return blockOrOutput


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
        inputs (list): Input connections.
        outputs (list): Output connections.
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
            raise AttributeError('%s has no inputs!' % self)

        return self.inputs[0]

    @property
    def output(self):
        """First output."""
        if not self.outputs:
            raise AttributeError('%s has no outputs!' % self)

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

    @functools.wraps(pipe_operator)
    def __ror__(self, output):
        # Reverse operands. Maintain order.
        return pipe_operator(output, self)

    __add__ = mix_operator

    @functools.wraps(mix_operator)
    def __radd__(self, output):
        # Reverse operands. Maintain order.
        return mix_operator(output, self)
