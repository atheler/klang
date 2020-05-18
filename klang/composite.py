"""Composite block."""
from klang.block import Block
from klang.connections import RelayBase
from klang.execution import determine_execution_order, execute


def introspect(composite):
    """Iterate over adjacent internal blocks of an composite via its in- and
    outgoing relay connections."""
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


class Composite(Block):

    """A composite is a collection of blocks which get bundled. Each composite
    has its own execution order of the internal blocks.
    """

    def __init__(self, nInputs=0, nOutputs=0, name=''):
        super().__init__(nInputs, nOutputs, name)
        self.execOrder = []

    def update_internal_exec_order(self):
        """Update execution order of composite."""
        execOrder = determine_execution_order(introspect(self))
        if self in execOrder:
            execOrder.remove(self)

        self.execOrder = execOrder

    def update(self):
        execute(self.execOrder)
