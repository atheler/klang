"""Connections.

Connectable input and output objects.

Two types of connections:
  - Value: Propagate some values from output to inputs. Gets updated every tick.
  - Message: Send discrete messages from an output to all connected inputs.

Relays can be used for block composites and they connect with inputs and
outputs.
"""
import collections

from klang.errors import KlangError


__all__ = ['Output', 'Relay', 'Input', 'MessageOutput', 'MessageRelay', 'MessageInput']


def is_valid_connection(output, input_):
    """Check if connection types are connectable."""
    validConnectionTypes = {
        OutputBase: (RelayBase, InputBase),
        RelayBase: (RelayBase, InputBase),
        Output: (Relay, Input),
        Relay: (Relay, Input),
        MessageOutput: (MessageRelay, MessageInput),
        MessageRelay: (MessageRelay, MessageInput),
    }
    validInputTypes = validConnectionTypes.get(type(output), ())
    return type(input_) in validInputTypes


def validate_connection(output, input_):
    """Validate connection coupling tuple.

    Raises:
        IncompatibleError: When it is not possible to connect output with
            input.
    """
    if not is_valid_connection(output, input_):
        fmt = 'Can not connect %s with %s!'
        msg = fmt % (type(output).__name__, type(input_).__name__)
        raise IncompatibleError(msg)


def validate_input_free(input_):
    """Validate if input_ is connectable."""
    if input_.connected:
        msg = '%s is already connected to another output!' % input_
        raise AlreadyConnectedError(msg)


class NotConnectedError(KlangError):

    """Connectable is not connected."""

    pass


class AlreadyConnectedError(KlangError):

    """Connectable already connected."""

    pass


class IncompatibleError(KlangError):

    """The two components can not be connected with each other."""

    pass


def make_connection(output, input_):
    """Make directional connection from output -> input_."""
    assert isinstance(output, OutputBase)
    assert isinstance(input_, InputBase)
    output.outgoingConnections.add(input_)
    input_.incomingConnection = output


def break_connection(output, input_):
    """Break directional connection from output -> input_."""
    assert isinstance(output, OutputBase)
    assert isinstance(input_, InputBase)
    output.outgoingConnections.remove(input_)
    input_.incomingConnection = None


class OutputBase:

    """Base class for all outputs."""

    def __init__(self, owner=None):
        self.owner = owner
        self.outgoingConnections = set()

    @property
    def connected(self):
        """Is connected to something?"""
        return bool(self.outgoingConnections)

    def connect(self, input_):
        """Connect with input."""
        validate_connection(self, input_)
        validate_input_free(input_)
        make_connection(self, input_)

    def disconnect(self, input_):
        """Disconnect input."""
        break_connection(self, input_)

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            'connected' if self.connected else 'not connected',
        )


class InputBase:

    """Base class for all inputs."""

    def __init__(self, owner=None):
        self.owner = owner
        self.incomingConnection = None

    @property
    def connected(self):
        """Is connected to something?"""
        return self.incomingConnection is not None

    def connect(self, output):
        """Connect with output."""
        validate_connection(output, self)
        validate_input_free(self)
        make_connection(output, self)

    def disconnect(self, output):
        """Disconnect output."""
        break_connection(output, self)

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            'connected' if self.connected else 'not connected',
        )


class RelayBase(InputBase, OutputBase):

    """Relay base. Can be used as input or output."""

    def __init__(self, owner=None):
        super().__init__(owner)
        self.outgoingConnections = set()

    def connect(self, other):
        if isinstance(other, InputBase):
            OutputBase.connect(self, other)
        else:
            InputBase.connect(self, other)

    def disconnect(self, other):
        if isinstance(other, InputBase):
            OutputBase.disconnect(self, other)
        else:
            InputBase.disconnect(self, other)


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

    """Value input."""

    def __init__(self, owner=None, value=0.):
        super().__init__(owner)
        _ValueContainer.__init__(self, value)

    @property
    def value(self):
        if self.connected:
            return self.incomingConnection.value

        return self._value

    def get_value(self):
        if self.connected:
            return self.incomingConnection.value

        return self._value


class Output(OutputBase, _ValueContainer):

    """Value output."""
    def __init__(self, owner=None, value=0.):
        super().__init__(owner)
        _ValueContainer.__init__(self, value)


class Relay(RelayBase, Input):

    """Value relay."""

    pass


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

    """Message input. Has message queue."""

    def __init__(self, owner=None):
        super().__init__(owner)
        _MessageQueue.__init__(self)


class MessageOutput(OutputBase):

    """Message output. Sends messages to connected message inputs."""

    def send(self, message):
        """Send message to all connected message inputs."""
        for con in self.outgoingConnections:
            con.push(message)


class MessageRelay(RelayBase, MessageOutput):

    """Message relay. Pass on all messages to connected inputs."""

    push = MessageOutput.send
