"""General mathematical helper functions."""
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
    """Clip value to [lower, upper]."""
    return min(max(value, lower), upper)


def is_power_of_two(number):
    """Check if number is power of two."""
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


def integrate(x, dt, y0=0.):
    """Numerical integration. Output is:

    y = integrate x with dt

    Args:
        x (array): Input array.
        dt (float): Time interval.

    Kwargs:
        y0 (float or array): Initial value of integrator.

    Returns:
        array: Integrated output array.
    """
    tmp = np.roll(x, 1, axis=0)
    tmp[0] = y0 / dt
    return dt * np.cumsum(tmp, axis=0)


def lcm(a, b):
    """Least common denominator."""
    return abs(a*b) // math.gcd(a, b)
