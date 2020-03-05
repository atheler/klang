"""Musical metre / time signature.

Metre classification.

Resources:
  - https://en.wikipedia.org/wiki/Metre_(music)
"""
import fractions

from klang.math import is_power_of_two, is_divisible


DUPLE = 2
"""int: A duplet."""

TRIPLE = 3
"""int: A triplet."""


def create_metre(numerator, denominator):
    """Create time signature fraction."""
    #if not isinstance(numerator, int):  # Fractional rhythms? 
    #    numerator = fractions.Fraction.from_float(numerator)
    return fractions.Fraction(numerator, denominator, _normalize=False)


FOUR_FOUR = create_metre(4, 4)
THREE_FOUR = WALTZ = create_metre(3, 4)
TWO_TWO = create_metre(2, 2)
SIX_EIGHT = create_metre(6, 8)


def is_irrational(metre):
    """Check if irrational metre."""
    return not is_power_of_two(metre.denominator)


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
    # What is a simple metre exactly?
    pass
