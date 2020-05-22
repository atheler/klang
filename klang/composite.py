"""Composite block."""
from klang.block import Block
from klang.connections import RelayBase
from klang.execution import determine_execution_order, execute


def introspect(composite):
    """Iterate over adjacent internal blocks of an composite via its in- and
    outgoing relay connections.
    """
    for relay in composite.inputs:
        if isinstance(relay, RelayBase):
            for input_ in relay.outgoingConnections:
                if input_.owner:
                    yield input_.owner

    for relay in composite.outputs:
        if isinstance(relay, RelayBase):
            output = relay.incomingConnection
            if output and output.owner:
                yield output.owner


def collect_connections(block):
    """Get all in- and outgoing connections of a block ((output, input) tuples).
    Exclude loop-around connections (block connected to itself).
    """
    for input_ in block.inputs:
        if input_.connected:
            src = input_.incomingConnection
            if src.owner is block:
                continue

            yield src, input_

    for output in block.outputs:
        for dst in output.outgoingConnections:
            if dst.owner is block:
                continue

            yield output, dst


class temporarily_unpatch:

    """Context manager for temporarily un- and repatching a block from its
    neighbors.

    Usage:
        >>> a = Block(0, 1, 'a')
        ... b = Block(1, 1, 'b')
        ... c = Block(1, 0, 'c')
        ... with temporarily_unpatch(b):
        ...     # Do some stuff with b
        ...     pass
        ... 
        ... # Connections are restored
    """

    def __init__(self, block):
        """Args:
            block (Block): Block to unpatch.
        """
        self.connections = list(collect_connections(block))

    def __enter__(self):
        """Temporarily unpatch."""
        for src, dst in self.connections:
            src.disconnect(dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Repatch as it was before."""
        for src, dst in self.connections:
            src.connect(dst)


class Composite(Block):

    """A composite is a collection of blocks which get bundled. Each composite
    has its own execution order of the internal blocks.
    """

    def __init__(self, name=''):
        super().__init__(nInputs=0, nOutputs=0, name=name)
        self.execOrder = []

    def update_internal_exec_order(self):
        """Update execution order of composite."""
        with temporarily_unpatch(self):
            execOrder = determine_execution_order(introspect(self))

        if self in execOrder:
            execOrder.remove(self)

        self.execOrder = execOrder

    def update(self):
        execute(self.execOrder)
