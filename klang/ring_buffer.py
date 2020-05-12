"""The missing ring buffer."""
import numpy as np


class RingBuffer:

    """Numpy ring buffer.

    Accessing the buffer over the turnaround point will result in a copy.

    TODO(atheler): Reimplement as double buffer?
    """

    def __init__(self, data, offset=0, copy=True):
        self.data = np.array(data, copy=copy)
        self.offset = offset

        self.readIdx = 0
        self.writeIdx = offset % self.length

    @classmethod
    def from_shape(cls, shape, offset=0):
        """Initialize empty ring buffer from shape."""
        data = np.zeros(shape)
        return cls(data, offset, copy=False)

    @property
    def length(self):
        """Length of ring buffer."""
        return self.data.shape[0]

    def write(self, frames):
        """Write some data to ring buffer."""
        start = self.writeIdx
        stop = (start + len(frames)) % self.length
        self.writeIdx = stop
        self[start:stop] = frames

    def read(self, nFrames):
        """Read `nFrames` from ring buffer."""
        start = self.readIdx
        stop = (start + nFrames) % self.length
        self.readIdx = stop
        return self[start:stop]

    def unpack_slice(self, slc):
        """Unpack slice `slice` in to tuple (start, stop, end)."""
        if slc.start is None:
            start = 0
        else:
            start = slc.start % self.length

        if slc.stop is None:
            stop = self.length
        else:
            stop = slc.stop % self.length

        if slc.step is None:
            step = 1
        else:
            step = slc.step

        return start, stop, step

    def __setitem__(self, key, value):
        #print('__setitem__(%s, %s)' % (key, value))
        if isinstance(key, slice):
            start, stop, step = self.unpack_slice(key)
            if start < stop:
                self.data[start:stop:step] = value
            else:
                try:
                    mid = (self.length - start) // step
                    self.data[start::step] = value[:mid]
                    self.data[:stop:step] = value[mid:]
                except TypeError:
                    self.data[start::step] = value
                    self.data[:stop:step] = value

        elif isinstance(key, int):
            self.data[key % self.length] = value

        else:
            self.data[key] = value

    def __getitem__(self, key):
        #print('__getitem__(%s)' % key)
        if isinstance(key, slice):
            start, stop, step = self.unpack_slice(key)
            if start < stop:
                return self.data[start:stop:step]

            return np.concatenate([
                self.data[start::step],
                self.data[:stop:step],
            ])

        if isinstance(key, int):
            return self.data[key % self.length]

        return self.data[key]
