"""Block and Connection operator overloading.

Logic / helper functions for operator overloading. pipe() and mix() operations.
Intended for the | and + symbol respectively. Defined its own module so that we
can reuse it with Blocks and Connections.

To be more explicit we import the Block class here (instead of a __hasattr__
check) and accept the circular import.
"""

from klang.errors import KlangError


class NotPipeable(KlangError):

    """Two objects are not pipeable because we can not extract an output and
    input.
    """

    pass


class NotMixable(KlangError):

    """Two objects are not mixable because we can not extract two outputs."""

    pass


def fetch_pipeable_connections(left, right):
    """Fetch output and input from left and right operands respectively."""
    # Circular import for comforts
    from klang.block import Block
    from klang.connections import OutputBase, InputBase

    try:
        if isinstance(left, Block):
            output = left.output
        else:
            output = left

        assert isinstance(output, OutputBase)

        if isinstance(right, Block):
            input_ = right.input
        else:
            input_ = right

        assert isinstance(input_, InputBase)

    except IndexError:
        msg = 'Can not pipe signal from %s to %s' % (left, right)
        raise NotPipeable(msg)

    return output, input_


def fetch_mixable_connections(left, right):
    """Fetch outputs from left and right operands respectively."""
    from klang.block import Block  # Circular import for comforts
    try:
        if isinstance(left, Block):
            leftOut = left.output
        else:
            leftOut = left

        if isinstance(right, Block):
            rightOut = right.output
        else:
            rightOut = right

    except IndexError:
        msg = 'Can not mix signals from %s and %s' % (left, right)
        raise NotMixable(msg)

    return leftOut, rightOut


def pipe(left, right):
    """Pipe signal from left to right no matter if Block or Connection
    instances.

    Args:
        left, right (Block or Connection): Left and right operands.

    Returns:
        Block: Right operand block.
    """
    output, input_ = fetch_pipeable_connections(left, right)
    output.connect(input_)
    return input_.owner


def mix(left, right):
    """Mix left and right together. No matter if Block or Connection instances.
    If left is already a Mixer connect right to it via a new channel.

    Args:
        left, right (Block or Connection): Left and right operands.

    Returns:
        Mixer: Current mono mixer instance of the operation.
    """
    from klang.audio.mixer import Mixer  # Circular import for comforts
    leftOut, rightOut = fetch_mixable_connections(left, right)

    if isinstance(left, Mixer):
        mixer = left
    else:
        mixer = Mixer(nInputs=1)
        leftOut.connect(mixer.inputs[0])

    mixer.add_channel()
    rightOut.connect(mixer.inputs[-1])
    return mixer
