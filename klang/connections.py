"""Connections.

Connectable input and output objects.
"""
import collections

from klang.errors import KlangError


MAX_MESSAGES = 50
"""int: Maximum number of messages on a queue."""


class NotConnectedError(KlangError):

    """Connectable is not connected."""

    pass


class AlreadyConnectedError(KlangError):

    """Connectable already connected."""

    pass


class Connectable:

    """Base class for connectable objects."""

    def __init__(self, owner, value=0., singleConnection=False):
        self.owner = owner
        self.value = value  # Also paceholder value for unconnected Input
        self.singleConnection = singleConnection
        self.connections = set()

    @property
    def connected(self):
        """Is connected?"""
        return bool(self.connections)

    def connect(self, other):
        """Make a connection to another connectable."""
        if self.singleConnection and self.connected:
            raise AlreadyConnectedError

        self.connections.add(other)
        other.connections.add(self)

    def disconnect(self, other):
        """Disconnect from another connectable."""
        self.connections.remove(other)
        other.connections.remove(self)

    def unplug(self):
        """Kill all connections."""
        for con in set(self.connections):
            self.disconnect(con)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def __str__(self):
        return '%s(%s, %s)' % (
            self.__class__.__name__,
            self.owner,
            'connected' if self.connected else 'not connected',
        )


class Input(Connectable):

    """Input slot.

    Can be connected to only one output.
    """

    def __init__(self, owner, value=0.):
        super().__init__(owner, value, singleConnection=True)

    def get_value(self):
        if not self.connected:
            return self.value

        output, = self.connections
        return output.value


class Output(Connectable):

    """Output slot.

    Holds the value. Can be connected to multiple inputs.
    """

    def connect(self, input):
        assert isinstance(input, Input)
        super().connect(input)


class MessageInput(Input):

    """Input for messages (Input where value attribute is a queue)."""

    def __init__(self, owner):
        super().__init__(
            owner,
            value=collections.deque(maxlen=MAX_MESSAGES),
        )

    def receive(self):
        """Iterate over received messages."""
        queue = self.get_value()
        while queue:
            yield queue.popleft()


class MessageOutput(Output):

    """Output for messages (Input where value attribute is a queue)."""

    def __init__(self, owner):
        super().__init__(
            owner,
            value=collections.deque(maxlen=MAX_MESSAGES),
            singleConnection=True,
        )

    def send(self, message):
        """Send message. No notificaiton."""
        queue = self.value
        queue.append(message)

    def receive(self):
        """Iterate over received messages."""
        queue = self.get_value()
        while queue:
            yield queue.popleft()
