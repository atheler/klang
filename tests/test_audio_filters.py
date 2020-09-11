import unittest
import math

import numpy as np
from numpy.testing import assert_equal

from klang.audio.filters import (
    USE_PYTHON_FALLBACK, PyForwardCombFilter, PyBackwardCombFilter, PyEchoFilter
)


if not USE_PYTHON_FALLBACK:
    from klang.audio.filters import (
        CForwardCombFilter, CBackwardCombFilter, CEchoFilter,
    )


K = 234
ALPHA = .9
BUFFER_SIZE = 123
assert K >= BUFFER_SIZE


def run_filter(filterType):
    """Run impulse through filter."""
    # Input impulse
    length = int(math.ceil(2 * K / BUFFER_SIZE)) * BUFFER_SIZE
    x = np.zeros(length)
    x[0] = 1.

    # Init and run filter
    fil = filterType(K, ALPHA)
    return np.concatenate([
        fil.filter(row) for row in x.reshape((-1, BUFFER_SIZE))
    ])


class TestCombFilters(unittest.TestCase):
    def test_python_forward_comb_filter(self):
        y = run_filter(PyForwardCombFilter)
        self.assertEqual(y[0], 1.)
        self.assertEqual(y[K], ALPHA)

    def test_python_backward_comb_filter(self):
        y = run_filter(PyBackwardCombFilter)
        self.assertEqual(y[0], 1.)
        self.assertEqual(y[K], ALPHA)

    if not USE_PYTHON_FALLBACK:
        def test_c_forward_comb_filter(self):
            y = run_filter(CForwardCombFilter)
            self.assertEqual(y[0], 1.)
            self.assertEqual(y[K], ALPHA)

        def test_c_backward_comb_filter(self):
            y = run_filter(CBackwardCombFilter)
            self.assertEqual(y[0], 1.)
            self.assertEqual(y[K], ALPHA)


class TestEchoFilters(unittest.TestCase):
    def test_python_echo_filter(self):
        y = run_filter(PyEchoFilter)
        self.assertEqual(y[0], 0.)
        self.assertEqual(y[K], 1.)
        self.assertEqual(y[2 * K], ALPHA)

    if not USE_PYTHON_FALLBACK:
        def test_c_echo_filter(self):
            y = run_filter(CEchoFilter)
            self.assertEqual(y[0], 0.)
            self.assertEqual(y[K], 1.)
            self.assertEqual(y[2 * K], ALPHA)


if __name__ == '__main__':
    unittest.main()
