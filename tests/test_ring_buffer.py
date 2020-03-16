import unittest

import numpy as np

from klang.ring_buffer import RingBuffer


class TestRingBuffer(unittest.TestCase):
    def setUp(self):
        self.ring = RingBuffer(np.arange(10))

    def test_getitem_with_index_and_wrap_around(self):
        for i in range(-10, 20):
            np.testing.assert_equal(self.ring[i], i % 10)

    def test_getitem_with_slice(self):
        np.testing.assert_equal(self.ring[:2], [0, 1])
        np.testing.assert_equal(self.ring[8:], [8, 9])
        np.testing.assert_equal(self.ring[2:8:2], [2, 4, 6])

    def test_getitem_with_slice_and_wrap_around(self):
        np.testing.assert_equal(self.ring[8:12], [8, 9, 0, 1])

    def test_setitem_single_value_with_slice_and_wrap_aroud(self):
        self.ring[8:14:2] = 666
        np.testing.assert_equal(self.ring.data, [666, 1, 666, 3, 4, 5, 6, 7, 666, 9])

    def test_setitem_multiple_values_with_slice_and_wrap_aroud(self):
        self.ring[8:14:2] = 42, 43, 44
        np.testing.assert_equal(self.ring.data, [43, 1, 44, 3, 4, 5, 6, 7, 42, 9])

    def test_write_read(self):
        data = np.zeros((10, 2))
        ring = RingBuffer(data)
        ring.write(np.ones((1, 2)))
        ring.write(np.ones((2, 2)) * 2)
        ring.write(np.ones((3, 2)) * 3)

        np.testing.assert_equal(ring.read(1), [[1, 1]])
        np.testing.assert_equal(ring.read(1), [[2, 2]])
        np.testing.assert_equal(ring.read(2), [[2, 2], [3, 3]])

    def test_stereo_delay_buffer(self):
        zeros = np.zeros((88200, 2))
        buf = RingBuffer(zeros, offset=44100)  # One second delay
        first = np.ones((44100, 2))
        buf.write(first)

        np.testing.assert_equal(buf.read(44100), zeros[:44100])

        second = 2 * np.ones((44100, 2))
        buf.write(second)

        np.testing.assert_equal(buf.read(44100), first)
        np.testing.assert_equal(buf.read(44100), second)


if __name__ == '__main__':
    unittest.main()
