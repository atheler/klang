"""Mathematical helper functions."""
import math

import numpy as np

from klang.constants import PI, TAU


def wrap(phase):
    """Wrap `phase` to the interval [-π, π)."""
    return (phase + PI) % TAU - PI


def normalize_values(array):
    """Normalize array values to [-1., 1.]."""
    maxAmplitude = np.abs(array).max()
    if maxAmplitude == 0:
        # TODO(atheler): Or just return array?
        raise ValueError('Zero amplitude! Can not normalize!')

    return array / maxAmplitude


def clip(value, lower, upper):
    """Clip value to [lower, upper]. Aka. clamp.

    Usage:
        >>> clip(-3, lower=-1, upper=2)
        -1
    """
    return min(max(value, lower), upper)


def is_power_of_two(number):
    """Check if number is power of two.

    Usage:
        >>> is_power_of_two(64)
        True

        >>> is_power_of_two(-3)
        False
    """
    if number <= 0:
        return False

    try:
        return number & (number - 1) == 0
    except TypeError:
        return False


def is_dyadic(fraction):
    """Check if dyadic rational."""
    return is_power_of_two(fraction.denominator)


def is_divisible(number, denominator):
    """Check if number is divisible by denominator."""
    return number % denominator == 0


def lcm(a, b):
    """Least common denominator."""
    return abs(a*b) // math.gcd(a, b)


def blend(a, b, x):
    """Dry / wet blend two signals together.

    Usage:
        >>> blend(np.zeros(4), np.ones(4), .5)
        array([0.5, 0.5, 0.5, 0.5])
    """
    return (1. - x) * a + x * b


def sign(number):
    """Math sign function."""
    return math.copysign(1., number)


def linear_mapping(xRange, yRange):
    """Get linear coefficients for y = a * x + b.

    Args:
        xRange (tuple): Input range (xmin, xmax).
        yRange (tuple): Output range (xmin, xmax).

    Returns:
        tuple: Linear coefficients a, b.
    """
    xmin, xmax = xRange
    ymin, ymax = yRange
    return np.linalg.solve([
        [xmin, 1.],
        [xmax, 1.],
    ], [ymin, ymax])
