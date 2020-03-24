"""Connections.

Connectable input and output objects.
"""
import collections

from klang.errors import KlangError


class AlreadyConnectedError(KlangError):

    """Connectable already connected."""

    pass


class NotConnectableError(KlangError):

    """The two components can not be connected with each other."""

    pass


class Connectable:

    """Base class for connectable objects.

    Attributes:
        owner (object): Owner object of connectable.
        singleConnection (bool): Maximum one connection possible.
        connections (set): Connected connectables.
    """

    def __init__(self, owner=None, singleConnection=False):
        self.owner = owner
        self.singleConnection = singleConnection

        self.connections = set()

    @property
    def connected(self):
        """Is connected?"""
        return bool(self.connections)

    def connect(self, other):
        """Make a connection to another connectable."""
        if (self.singleConnection and self.connected)\
            or (other.singleConnection and other.connected):
            raise AlreadyConnectedError

        self.connections.add(other)
        other.connections.add(self)

    def disconnect(self, other):
        """Disconnect from another connectable."""
        self.connections.remove(other)
        other.connections.remove(self)

    def __str__(self):
        return '%s(%s, %s)' % (
            self.__class__.__name__,
            self.owner,
            'connected' if self.connected else 'not connected',
        )


class _Input(Connectable):

    """Input connection base class."""

    def __init__(self, owner=None):
        super().__init__(owner, singleConnection=True)

    def connect(self, output):
        """Connect with an output."""
        if not isinstance(output, _Output):
            raise NotConnectableError('Input can only connect to a output!')

        super().connect(output)


class _Output(Connectable):

    """Output connection base class."""

    def connect(self, input):
        """Connect with an input."""
        if not isinstance(input, _Input):
            raise NotConnectableError('Output can only connect to inputs!')

        super().connect(input)


class _ValueContainer:

    """Value attribute mixin class."""

    def __init__(self, value=0.):
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
        """Set value."""
        return self._value

    def set_value(self, value):
        """Get value."""
        self._value = value


class Input(_Input, _ValueContainer):

    """Input slot.

    Can be connected to only one output.
    """

    def __init__(self, owner=None, value=0.):
        super().__init__(owner=owner)
        _ValueContainer.__init__(self, value=value)

    @property
    def value(self):
        """Get value either from connected output or from this input itself."""
        if self.connected:
            output, = self.connections
            return output._value

        return self._value

    @value.setter
    def value(self, value):
        # Needs to be overwritten. We do not inherit @value.setter from
        # _ValueContainer!
        self._value = value

    def get_value(self):
        if self.connected:
            output, = self.connections
            return output._value

        return self._value


class Output(_Output, _ValueContainer):

    """Output slot.

    Holds the value. Can be connected to multiple inputs.
    """

    def __init__(self, owner=None, value=0.):
        super().__init__(owner=owner)
        _ValueContainer.__init__(self, value=value)


class _MessageQueue:

    """Message queue mixin class."""

    MAX_MESSAGES = 50
    """int: Maximum number of messages on a queue."""

    def __init__(self):
        self.queue = collections.deque(maxlen=self.MAX_MESSAGES)

    def push(self, message):
        """Push message on the message queue."""
        self.queue.append(message)


class MessageInput(_Input, _MessageQueue):

    """Input for messages (Input where value attribute is a queue)."""

    def __init__(self, owner=None):
        super().__init__(owner=owner)
        _MessageQueue.__init__(self)

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


class MessageOutput(_Output):

    """Output for messages (Input where value attribute is a queue)."""

    def send(self, message):
        """Send message. No notificaiton."""
        for con in self.connections:
            con.push(message)
