"""Signals over network blocks."""
import base64
import json
import logging
import socket

import numpy as np

from klang.block import Block
from klang.connections import MessageOutput, MessageInput
from klang.messages import Note


NETWORK_BUFFER_SIZE = 1024
"""int: Network buffer size for receiving datagram messages."""

LOGGER = logging.getLogger(__name__)
"""Logger: Network module logger."""


def create_socket_from_address(address):
    """Create new socket. Deduce socket family from address. Non-blocking.

    Args:
        address (tuple, str): Either host, port tuple for IP or str for UNIX
            socket address.

    Returns:
        socket.socket: Fresh socket.
    """
    if isinstance(address, tuple):
        family = socket.AF_INET
    elif isinstance(address, str):
        family = socket.AF_UNIX
    else:
        msg = 'Can not deduce socket family from address %r' % address
        raise ValueError(msg)

    sock = socket.socket(family, type=socket.SOCK_DGRAM)
    sock.setblocking(False)
    return sock


def receive_all_from(sock, bufsize=NETWORK_BUFFER_SIZE):
    """Receive all data from a socket and yield raw bytes.

    Args:
        sock (socket.socket): Readable non-blocking socket.
        bufsize (int): Number of bytes to read per recv call.

    Yields:
        bytes: Received data chunks.
    """
    try:
        # This would be a use case for the Walrus Operator but we want support
        # for <3.8
        data = sock.recv(bufsize)
        while data:
            if len(data) == bufsize:
                fmt = 'Full input buffer (%d bytes)! Overflow?'
                LOGGER.warning(fmt, bufsize)

            yield data
            data = sock.recv(bufsize)
    except BlockingIOError:
        return


def array_to_dict(arr):
    """Convert numpy array to JSON compatible dictionary using base 64
    encoding.
    """
    raw = base64.b64encode(arr.data)
    return {
        'type': 'ndarray',
        'dtype': str(arr.dtype),
        'shape': arr.shape,
        'data': raw.decode(),
    }


def array_from_dict(dct):
    """Reconstruct numpy array from base 64 dictionary representation."""
    data = base64.b64decode(dct['data'])
    return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])


def klang_object_hook(obj):
    """JSON object hook for Klang objects."""
    type_ = obj.get('type')
    if type_ == 'Note':
        return Note.from_dict(obj)

    if type_ == 'ndarray':
        return array_from_dict(obj)

    return obj


class KlangJSONEncoder(json.JSONEncoder):

    """JSONEncoder with support for Klang objects.

    Technical Note:
        Providing a custom default(self, o) function to
        json.JSONEncoder(default=default) wont work for custom types which
        inherit from a encodable base type (e.g. namedtuple). We therefore have
        to override encode() method. See https://bugs.python.org/issue30343.
    """

    def encode(self, o):
        if isinstance(o, Note):
            return o.to_json()

        if isinstance(o, np.ndarray):
            dct = array_to_dict(o)
            return super().encode(dct)

        return super().encode(o)


class JsonCourier:

    """JSON sender / receiver worker class. Handles socket connection and data
    en-/ decoding.
    """

    def __init__(self, address, bind=False, object_hook=klang_object_hook):
        """Args:
            address (tuple or str): Socket address.

        Kwargs:
            bind (bool): If to bind socket to address (receiving).
            object_hook (function): Object hook function for JSON decoder.
        """
        self.address = address
        self.sock = create_socket_from_address(address)
        self.encoder = KlangJSONEncoder()
        self.decoder = json.JSONDecoder(object_hook=object_hook)
        self.logger = logging.getLogger(type(self).__name__)
        if bind:
            self.logger.info('Binding address %s', self.address)
            self.sock.bind(self.address)

    def receive_objects(self):
        """Yields all JSON decoded objects."""
        for data in receive_all_from(self.sock):
            #print('Received:', data)
            string = data.decode()
            while string:
                try:
                    obj, stop = self.decoder.raw_decode(string)
                    yield obj
                    string = string[stop:]
                except json.JSONDecodeError as err:
                    self.logger.error(err, exc_info=True)
                    break

    def send_object(self, obj):
        """Send object to address as JSON."""
        string = self.encoder.encode(obj)
        data = string.encode()
        #print('Sending', data)
        return self.sock.sendto(data, self.address)

    def __del__(self):
        self.logger.info('Closing socket %s', self.sock)
        self.sock.close()


class NetworkIn(Block):

    """Network value receiver block."""

    def __init__(self, address):
        """Args:
            address (tuple or str): Network address.
        """
        super().__init__(nOutputs=1)
        self.courier = JsonCourier(address, bind=True)

    def update(self):
        for obj in self.courier.receive_objects():
            self.output.set_value(obj)


class NetworkMessageIn(Block):

    """Network message receiver block."""

    def __init__(self, address):
        """Args:
            address (tuple or str): Network address.
        """
        super().__init__()
        self.outputs = [MessageOutput(owner=self)]
        self.courier = JsonCourier(address, bind=True)

    def update(self):
        for obj in self.courier.receive_objects():
            self.output.send(obj)


class NetworkOut(Block):

    """Network value sender block."""

    def __init__(self, address):
        """Args:
            address (tuple or str): Network address.
        """
        super().__init__(nInputs=1)
        self.courier = JsonCourier(address)

    def update(self):
        value = self.input.value
        self.courier.send_object(value)


class NetworkMessageOut(Block):

    """Network message sender block."""

    def __init__(self, address):
        """Args:
            address (tuple or str): Network address.
        """
        super().__init__()
        self.inputs = [MessageInput(owner=self)]
        self.courier = JsonCourier(address)

    def update(self):
        for msg in self.input.receive():
            self.courier.send_object(msg)
