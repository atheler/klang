import numpy as np


class RingBuffer:

    """Numpy ring buffer."""

    def __init__(self, shape, offset=0, *args, **kwargs):
        self.data = np.zeros(shape, *args, **kwargs)
        self.readIdx = 0
        self.writeIdx = offset % self.length

    @property
    def length(self):
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