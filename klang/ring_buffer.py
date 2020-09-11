"""The missing ring buffer."""
from typing import Tuple, Sequence

import numpy as np

from klang.config import BUFFER_SIZE
from klang.constants import MONO


class RingBuffer:

    """Circular sample buffer.

    Supports extending by multiple values. Over allocates bufferSize many
    samples so that we have enough space for new samples at a given read / write
    position.
    """

    def __init__(self, length: int, capacity: int = None, bufferSize:
                 int = BUFFER_SIZE, nChannels: int = MONO, dtype: type = float):
        """Args:
            length: Length of ring buffer.

        Kwargs:
            capacity: Maximum ring buffer capacity. Same as length by default.
            bufferSize: Amount of over allocation. Should be as big as largest
                maximum number of samples.
            nChannels: Number of audio channels.
            dtype: Buffer data type.
        """
        if capacity is None:
            capacity = length

        self._length = length
        self.capacity = capacity
        self.bufferSize = bufferSize

        shape: list = [capacity + bufferSize]
        if nChannels > MONO:
            shape.append(nChannels)

        self.data = np.zeros(shape, dtype)
        self.pos = 0

    @property
    def length(self) -> int:
        """Get current length."""
        return self._length

    @length.setter
    def length(self, value: int):
        """Set new length (and adjust current read / write position). Can not be
        bigger than allocated max capacity.
        """
        if value > self.capacity:
            msg = f'New length {value} larger than max capacity {self.capacity}!'
            raise ValueError(msg)

        self._length = value
        self.pos %= value

    def peek(self, nValues: int = None) -> np.ndarray:
        """Peek into current buffer content. Returns no copy!"""
        if nValues is None:
            nValues = self.bufferSize

        start = self.pos
        stop = start + nValues
        return self.data[start:stop]

    def append(self, value: float):
        """Append single value to RingBuffer."""
        self.data[self.pos] = value
        if self.pos < self.bufferSize:
            # Copy to tail as well
            self.data[self.pos + self.length] = value

        if self.pos > self.length:
            # Copy to head as well
            self.data[self.pos - self.length] = value

        self.pos += 1
        self.pos %= self._length

    def extend(self, values: Sequence[float]):
        """Extend RingBuffer with multiple values."""
        nValues = len(values)
        if nValues > self.bufferSize:
            raise ValueError('To many samples!')

        start = self.pos
        stop = start + nValues
        self.data[start:stop] = values
        if start < self.bufferSize:
            # Copy to tail as well
            a = start + self._length
            b = min(self._length + self.bufferSize, stop + self._length)
            self.data[a:b] = values[:b-a]  # Pick first (b-a) values

        if stop > self._length:
            # Copy to head as well
            a = max(0, start - self._length)
            b = stop - self._length
            self.data[a:b] = values[-(b-a):]  # Pick last (b-a) values

        self.pos += nValues
        self.pos %= self._length

    def peek_extend(self, values: Sequence[float]) -> np.ndarray:
        """Pop some samples from buffer before overwriting them with the new values."""
        ret = self.peek(nValues=len(values)).copy()
        self.extend(values)
        return ret

    def __repr__(self) -> str:
        infos = [
            'length=%d' % self.length,
        ]
        if self.length < self.capacity:
            infos.append('capacity=%d' % self.capacity)

        return f"{type(self).__qualname__}({', '.join(infos)})"
