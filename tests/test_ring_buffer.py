import unittest

import numpy as np
from numpy.testing import assert_equal

from klang.ring_buffer import RingBuffer


class TestRingBuffer(unittest.TestCase):
    def test_data(self):
        ring = RingBuffer(7, bufferSize=4)

        assert_equal(ring.data, 11 * [0.])
        self.assertEqual(ring.pos, 0)

    def test_appending(self):
        ring = RingBuffer(7, bufferSize=4)
        for i in range(5):
            ring.append(10 + i)

        self.assertEqual(ring.pos, 5)
        assert_equal(ring.data, [
            10, 11, 12, 13, 14, 0, 0,  # Main memory
            10, 11, 12, 13,  # Over allocated shadow memory
        ])

    def test_extending(self):
        ring = RingBuffer(7, bufferSize=4)

        self.assertEqual(ring.pos, 0)
        assert_equal(ring.data, [
            0., 0., 0., 0., 0., 0., 0.,  # Main memory
            0., 0., 0., 0.,  # Over allocated shadow memory
        ])

        ring.extend([1, 2, 3, 4])

        self.assertEqual(ring.pos, 4)
        assert_equal(ring.data, [
            1., 2., 3., 4., 0., 0., 0.,  # Main memory
            1., 2., 3., 4.,  # Over allocated shadow memory
        ])

        ring.extend([11, 12, 13, 14])

        self.assertEqual(ring.pos, 1)
        assert_equal(ring.data, [
            14., 2., 3., 4., 11., 12., 13.,  # Main memory
            14., 2., 3., 4.,  # Over allocated shadow memory
        ])

        ring.extend([111, 112, 113, 114])

        self.assertEqual(ring.pos, 5)
        assert_equal(ring.data, [
            14., 111., 112., 113., 114., 12., 13.,  # Main memory
            14., 111., 112., 113.,  # Over allocated shadow memory
        ])

    def test_extending_with_less_than_buffer_size(self):
        ring = RingBuffer(7, bufferSize=4)
        ring.extend([0.])
        ring.extend([1., 2.])
        ring.extend([3., 4., 5.])
        ring.extend([6., 7.])

        assert_equal(ring.data, [
            7., 1., 2., 3., 4., 5., 6.,
            7., 1., 2., 3.
        ])

    def test_extending_with_to_many_samples(self):
        ring = RingBuffer(7, bufferSize=4)
        with self.assertRaises(ValueError):
            ring.extend([1, 2, 3, 4, 5])

    def test_peeking(self):
        ring = RingBuffer(7, bufferSize=4)

        assert_equal(ring.peek(), [0, 0, 0, 0])

        ring.extend([1, 2, 3, 4])

        assert_equal(ring.peek(), [0, 0, 0, 1])

        ring.extend([5, 6, 7, 8])

        assert_equal(ring.peek(), [2, 3, 4, 5])

    def test_to_long(self):
        bufSize = 4
        ring = RingBuffer(7, bufferSize=bufSize)
        with self.assertRaises(ValueError):
            ring.length = 2 * bufSize

    def test_peek_extend(self):
        ring = RingBuffer(7, bufferSize=4)

        assert_equal(ring.peek_extend([1, 2, 3, 4]), [0, 0, 0, 0])
        assert_equal(ring.peek_extend([5, 6, 7, 8]), [0, 0, 0, 1])
        assert_equal(ring.peek_extend([9, 10, 11, 12]), [2, 3, 4, 5])

    def test_delay_line_with_impulse(self):
        bufSize = 4

        # Delay of 7 samples
        ring = RingBuffer(7, bufferSize=bufSize)
        x = np.array([1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.])
        desired = [0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        blocks = [
            ring.peek_extend(row)
            for row in x.reshape((-1, bufSize))
        ]
        y = np.concatenate(blocks)

        assert_equal(y, desired)

    def test_stereo_delay_line_with_impulse(self):
        ring = RingBuffer(7, bufferSize=4, nChannels=2)
        audio = np.array([
            [1., 0.],
            [0., 1.],
            [0., 0.],
            [0., 0.],
        ])
        silence = np.zeros((4, 2))

        assert_equal(ring.peek_extend(audio), [[0, 0], [0, 0], [0, 0], [0, 0]])
        assert_equal(ring.peek_extend(silence), [[0, 0], [0, 0], [0, 0], [1, 0]])
        assert_equal(ring.peek_extend(silence), [[0, 1], [0, 0], [0, 0], [0, 0]])

    def test_reducing_length(self):
        ring = RingBuffer(7, bufferSize=4)
        impulse = np.array([1., 0., 0., 0.])
        silence = np.zeros(4)

        assert_equal(ring.peek_extend(impulse), [0., 0., 0., 0.])
        assert_equal(ring.peek_extend(silence), [0., 0., 0., 1.])
        assert_equal(ring.peek_extend(silence), [0., 0., 0., 0.])

        ring.length = 5
        ring.pos = 2  # Test non zero pos

        assert_equal(ring.peek_extend(silence), [0., 0., 0., 0.])
        assert_equal(ring.peek_extend(impulse), [0., 0., 0., 0.])
        assert_equal(ring.peek_extend(silence), [0., 1., 0., 0.])


if __name__ == '__main__':
    unittest.main()
