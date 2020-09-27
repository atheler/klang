"""Connections.

Connectable outputs and inputs objects. In general it is always possible to
connect one output to multiple inputs but not the other way round.

A connection is a (output, input) tuple.

There are two types of connections:
  - Value: Propagate some value through the connections in very tick
    (corresponds to continuous data stream).
  - Message: Send discrete messages from an output to all connected inputs.

Relays can be used to pass on data from an output to inputs. They are used as
the gateway between the outside and the inside world when building composite
blocks. They work as an output and an input at the same time. E.g. Output ->
Relay -> Input (note that there can be multiple relays between an output and an
input).

"""
import collections
import itertools

from klang.errors import KlangError


__all__ = [
    'Output', 'Relay', 'Input', 'MessageOutput', 'MessageRelay', 'MessageInput',
]


class InputAlreadyConnected(KlangError):

    """Can not connect to already connected input."""


class IncompatibleConnection(KlangError):

    """The two components can not be connected with each other."""


def is_valid_connection(output, input_):
    """Check if connection types are connectable."""
    outputType = type(output)
    inputType = type(input_)
    validConnectionTypes = {
        # Base classes
        (OutputBase, RelayBase),
        (OutputBase, InputBase),
        (RelayBase, RelayBase),
        (RelayBase, InputBase),

        # Value classes
        (Output, Relay),
        (Output, Input),
        (Relay, Relay),
        (Relay, Input),

        # Message classes
        (MessageOutput, MessageRelay),
        (MessageOutput, MessageInput),
        (MessageRelay, MessageRelay),
        (MessageRelay, MessageInput),
    }

    return (outputType, inputType) in validConnectionTypes


def validate_connection(output, input_):
    """Validate connection coupling tuple.

    Raises:
        IncompatibleConnection: When it is not possible to connect output with
            input.
    """
    if not is_valid_connection(output, input_):
        fmt = 'Can not connect %s with %s!'
        msg = fmt % (type(output).__name__, type(input_).__name__)
        raise IncompatibleConnection(msg)


def make_connection(output, input_):
    """Make directional connection from output -> input_."""
    validate_connection(output, input_)
    if input_.connected:
        msg = '%s is already connected to another output!' % input_
        raise InputAlreadyConnected(msg)

    # Make the actual connection
    output.outgoingConnections.add(input_)
    input_.incomingConnection = output


def break_connection(output, input_):
    """Break directional connection from output -> input_."""
    validate_connection(output, input_)

    # Break the actual connection
    output.outgoingConnections.remove(input_)
    input_.incomingConnection = None


def is_connected(output, input_):
    """Check if output is connected to input_."""
    if not is_valid_connection(output, input_):
        return False

    return output is input_.incomingConnection and input_ in output.outgoingConnections


def are_connected(*connectables):
    """Check if each pair in a chain of connectalbes are connected to each
    other.
    """
    # Iterate over pairs
    outputs, inputs = itertools.tee(connectables)
    next(inputs, None)
    for output, input_ in zip(outputs, inputs):
        if not is_connected(output, input_):
            return False

    return True


def str_function(connectable):
    """__str__ function for OutputBase and InputBase."""
    infos = []
    if connectable.owner:
        infos.append('owner: %s' % connectable.owner)

    if connectable.connected:
        infos.append('connected')
    else:
        infos.append('not connected')

    return '%s(%s)' % (type(connectable).__name__, ', '.join(infos))


class OutputBase:

    """Base class for all outputs.

    Attributes:
        owner (Block): Parent block owning connection.
        outgoingConnections (set): All connected InputBases.
    """

    def __init__(self, owner=None):
        """Kwargs:
            owner (Block): Parent block owning this output.
        """
        self.owner = owner
        self.outgoingConnections = set()

    @property
    def connected(self):
        """Is connected to at least one input?"""
        return bool(self.outgoingConnections)

    def connect(self, input_):
        """Connect with input."""
        make_connection(self, input_)

    def disconnect(self, input_):
        """Disconnect input."""
        break_connection(self, input_)

    __str__ = str_function


class InputBase:

    """Base class for all inputs.

    Attributes:
        owner (Block): Parent block owning connection.
        incomingConnection (OutputBase): Connected OutputBase.
    """

    def __init__(self, owner=None):
        """Kwargs:
            owner (Block): Parent block owning this input.
        """
        self.owner = owner
        self.incomingConnection = None

    @property
    def connected(self):
        """Is connected to an output?"""
        return self.incomingConnection is not None

    def connect(self, output):
        """Connect with output."""
        make_connection(output, self)

    def disconnect(self, output):
        """Disconnect output."""
        break_connection(output, self)

    __str__ = str_function


class RelayBase(InputBase, OutputBase):

    """Relay base.

    Connection type for composite blocks. Connects the outside world with the
    internal composite blocks. Kind of like an input and output at the same time
    depending on the perspective.
    """

    def __init__(self, owner=None):
        super().__init__(owner)
        OutputBase.__init__(self, owner)

    def connect(self, other):
        """Connect to another connectable.

        Args:
            other (OutputBase, InputBase, RelayBase): Connectable instance.
        """
        # pylint: disable=arguments-differ
        if isinstance(other, InputBase):
            make_connection(self, other)
        else:
            make_connection(other, self)

    def disconnect(self, other):
        """Disconnect from another connectable.

        Args:
            other (OutputBase, InputBase, RelayBase): Connectable instance.
        """
        # pylint: disable=arguments-differ
        if isinstance(other, InputBase):
            break_connection(self, other)
        else:
            break_connection(other, self)


class _ValueContainer:

    """Value attribute mixin class.

    Can not decide between property/setter vs. conventional getters and setters.
    With value fetching a property looks nice (data = input.value) with value
    propagating a setter looks better (output.set_value(data)).
    """

    def __init__(self, value=0.):
        """Kwargs:
            value (object): Initial value.
        """
        self._value = value

    @property
    def value(self):
        """Get value."""
        return self._value

    @value.setter
    def value(self, value):
        """Set value."""
        self._value = value

    def get_value(self):
        """Get value."""
        return self._value

    def set_value(self, value):
        """Set value."""
        self._value = value


class Input(InputBase, _ValueContainer):

    """Value input. Will fetch value from connected output. Also has its own
    _value attribute as a fallback when not connected.
    """

    def __init__(self, owner=None, value=0.):
        super().__init__(owner)
        _ValueContainer.__init__(self, value)

    @property
    def value(self):
        """Try to fetch value from connected output."""
        if self.connected:
            return self.incomingConnection.value

        return self._value

    @value.setter
    def value(self, value):
        """Set value."""
        self._value = value

    def get_value(self):
        """Try to fetch value from connected output."""
        if self.connected:
            return self.incomingConnection.value

        return self._value


class Output(OutputBase, _ValueContainer):

    """Value output. Will propagate its value to connected inputs."""

    def __init__(self, owner=None, value=0.):
        super().__init__(owner)
        _ValueContainer.__init__(self, value)


class Relay(RelayBase, Input):

    """Value relay. Passes value from connected output to all connected
    inputs.
    """


class _MessageQueue:

    """Message queue mixin class."""

    MAX_MESSAGES = 50
    """int: Maximum number of messages on a queue."""

    def __init__(self):
        self.queue = collections.deque(maxlen=self.MAX_MESSAGES)

    def push(self, message):
        """Push message on the message queue."""
        self.queue.append(message)

    def receive(self):
        """Iterate over received messages."""
        while self.queue:
            yield self.queue.popleft()

    def receive_latest(self):
        """Return latest received messages (if any). Discard the rest."""
        if not self.queue:
            return None

        latestMsg = self.queue.pop()
        self.queue.clear()
        return latestMsg


class MessageInput(InputBase, _MessageQueue):

    """Message input. Has its own message queue where it receives from a
    connected MessageOutput.
    """

    def __init__(self, owner=None):
        super().__init__(owner)
        _MessageQueue.__init__(self)


class MessageOutput(OutputBase):

    """Message output. Sends messages to all connected message inputs."""

    def send(self, message):
        """Send message to all connected message inputs."""
        for con in self.outgoingConnections:
            con.push(message)


class MessageRelay(RelayBase, MessageOutput):

    """Message relay. Passes on all messages from a connected MessageOutput to
    all connected MessageInputs.
    """

    push = MessageOutput.send
