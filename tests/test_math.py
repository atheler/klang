import unittest

from klang.math import linear_mapping


class TestLinearMapping(unittest.TestCase):
    def test_value_range(self):
        xmin, xmax = xRange = (-1, 2)
        ymin, ymax = yRange = (-2, 3)

        a, b = linear_mapping(xRange, yRange)

        self.assertEqual(a * xmin + b, ymin)
        self.assertEqual(a * xmax + b, ymax)


if __name__ == '__main__':
    unittest.main()
