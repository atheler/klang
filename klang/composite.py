"""Composite block."""
import contextlib

from klang.block import Block, collect_connections
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


@contextlib.contextmanager
def temporarily_unpatch(block):
    """Context manager to temporarily unpatch block its input and output
    neighbors.

    Usage:
        >>> a = Block(0, 1, 'a')
        ... b = Block(1, 1, 'b')
        ... c = Block(1, 0, 'c')
        ... a | b | c
        ... with temporarily_unpatch(b):
        ...     # Do some stuff with b
        ...     pass
        ... 
        ... # Connections are restored
    """
    connections = list(collect_connections(block))
    for src, dst in connections:
        src.disconnect(dst)

    yield block

    for src, dst in connections:
        src.connect(dst)


class Composite(Block):

    """A composite is a collection of blocks which get bundled. Each composite
    has its own execution order of the internal blocks.
    """

    def __init__(self, nInputs=0, nOutputs=0, name=''):
        super().__init__(nInputs, nOutputs, name)
        self.execOrder = []

    def update_internal_exec_order(self, *blocks):
        """Update execution order of composite. Uses "introspected" blocks by
        default (internally connected blocks via relays).

        Args:
            blocks (Block): Starting blocks.
        """
        if not blocks:
            blocks = introspect(self)

        with temporarily_unpatch(self):
            execOrder = determine_execution_order(blocks)

        while self in execOrder:
            execOrder.remove(self)

        self.execOrder = execOrder

    def update(self):
        """Execute internal composite blocks."""
        execute(self.execOrder)
