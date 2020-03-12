"""Musical metre / time signature.

Metre classification.

Resources:
  - https://en.wikipedia.org/wiki/Metre_(music)
"""
import fractions

from klang.math import is_dyadic, is_divisible


DUPLE = 2
"""int: A duplet."""

TRIPLE = 3
"""int: A triplet."""

QUAD = 4
"""int: ???"""


def create_metre(numerator, denominator=None):
    """Create time signature fraction. Normal Fraction with no normalization.

    Args:
        numerator (int, float or str): Numerator.

    Kwargs:
        denominator (int): Denominator.

    Returns:
        Fraction: Metre / time signature.
    """
    #if not isinstance(numerator, int):  # Fractional rhythms? 
    #    numerator = fractions.Fraction.from_float(numerator)
    return fractions.Fraction(numerator, denominator, _normalize=False)


FOUR_FOUR_METRE = create_metre(4, 4)
"""Fraction: 4 / 4 time signature."""

THREE_FOUR_METRE = WALTZ_METRE = create_metre(3, 4)
"""Fraction: 3 / 4 time signature."""

TWO_FOUR_METRE = create_metre(2, 4)
"""Fraction: 2 / 4 time signature."""

TWO_TWO_METRE = create_metre(2, 2)
"""Fraction: 2 / 2 time signature."""

SIX_EIGHT_METRE = create_metre(6, 8)
"""Fraction: 6 / 8 time signature."""

NINE_EIGHT_METRE = create_metre(9, 8)
"""Fraction: 9 / 8 time signature."""


def is_irrational(metre):
    """Check if irrational metre."""
    return not is_dyadic(metre)


assert not is_irrational(create_metre(3, 4))
assert is_irrational(create_metre(3, 5))


def is_fractional(metre):
    """Check if fractional metre."""
    return metre.numerator % 1 != 0  # TODO(atheler): Kind of redundant in this fraction based setting.


def is_complex(metre):
    """Check if complex metre (e.g. 7/8)."""
    if is_divisible(metre.numerator, DUPLE):
        return False

    if is_divisible(metre.numerator, TRIPLE):
        return False

    return True


assert not is_complex(create_metre(4, 4))
assert not is_complex(create_metre(3, 4))
assert not is_complex(create_metre(6, 8))
assert is_complex(create_metre(5, 4))
assert is_complex(create_metre(7, 8))


def is_compound(metre):
    """Check if compound metre. E.g. 6/8, 9/8."""
    if metre.numerator < 6:
        return False

    return is_divisible(metre.numerator, TRIPLE)


assert is_compound(create_metre(6, 8))
assert is_compound(create_metre(9, 8))
assert is_compound(create_metre(12, 8))
assert not is_compound(create_metre(3, 4))
assert not is_compound(create_metre(4, 4))


def is_simple(metre):
    """Check if simple metre."""
    return metre.numerator in {DUPLE, TRIPLE, QUAD}


assert is_simple(create_metre(4, 4))
assert is_simple(create_metre(3, 4))
assert is_simple(create_metre(2, 4))
assert is_simple(create_metre(3, 8))
assert is_simple(create_metre(2, 2))
assert not is_simple(create_metre(6, 8))
assert not is_simple(create_metre(12, 8))
assert not is_simple(create_metre(9, 4))
