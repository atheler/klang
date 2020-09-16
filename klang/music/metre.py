"""Musical metre / time signature.

Metre classification.

Resources:
  - https://en.wikipedia.org/wiki/Metre_(music)
"""
from fractions import Fraction

from klang.math import is_dyadic, is_divisible


DUPLE: int = 2
"""int: A duplet."""

TRIPLE: int = 3
"""int: A triplet."""

QUAD: int = 4
"""int: ???"""


def create_metre(numerator: int, denominator: int = None) -> Fraction:
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
    return Fraction(numerator, denominator, _normalize=False)


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

SEVEN_EIGHT_METRE = create_metre(7, 8)
"""Fraction: 7 / 8 time signature."""

NINE_EIGHT_METRE = create_metre(9, 8)
"""Fraction: 9 / 8 time signature."""


def is_irrational(metre: Fraction) -> bool:
    """Check if irrational metre."""
    return not is_dyadic(metre)


def is_fractional(metre: Fraction) -> bool:
    """Check if fractional metre."""
    return metre.numerator % 1 != 0  # TODO(atheler): Kind of redundant in this fraction based setting.


def is_complex(metre: Fraction) -> bool:
    """Check if complex metre (e.g. 7/8)."""
    if is_divisible(metre.numerator, DUPLE):
        return False

    if is_divisible(metre.numerator, TRIPLE):
        return False

    return True


def is_compound(metre: Fraction) -> bool:
    """Check if compound metre. E.g. 6/8, 9/8."""
    if metre.numerator < 6:
        return False

    return is_divisible(metre.numerator, TRIPLE)


def is_simple(metre: Fraction) -> bool:
    """Check if simple metre."""
    return metre.numerator in {DUPLE, TRIPLE, QUAD}


def default_beat_value(metre: Fraction) -> Fraction:
    """Default / "best guess" beat value for a given metre.

    Args:
        metre (Fraction): Time signature.

    Returns:
        Fraction: Beat value.

    Usage:
        >>> simple = create_metre(4, 4)
        ... default_beat_value(simple)
        Fraction(1, 4)

        >>> waltz = create_metre(3, 4)
        ... default_beat_value(waltz)
        Fraction(1, 4)

        >>> compound = create_metre(6, 8)
        ... default_beat_value(compound)
        Fraction(3, 4)

        >>> complex_ = create_metre(7, 8)
        ... default_beat_value(complex_)
        Fraction(2, 8)
    """
    if is_compound(metre):
        return create_metre(3, metre.denominator)

    if is_complex(metre):
        return create_metre(2, metre.denominator)

    return create_metre(1, metre.denominator)


def number_of_beats(metre: Fraction, beatValue: Fraction = None) -> int:
    """Number of beats in a bar."""
    if beatValue is None:
        beatValue = default_beat_value(metre)

    return metre / beatValue
