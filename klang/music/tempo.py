"""Tempo of music."""
from klang.constants import TAU
from klang.music.metre import (
    FOUR_FOUR_METRE, is_compound, create_metre, is_complex
)


def tempo_2_frequency(tempo):
    """Convert beats per minute (BPM) to frequency."""
    minute = 60.
    return tempo / minute


def default_beat_value(metre):
    """Default / "best guess" beat value for a given metre.

    Usage:
        >>> default_beat_value(create_metre(4, 4))
        Fraction(1, 4)

        >>> default_beat_value(create_metre(3, 4))
        Fraction(1, 4)

        >>> default_beat_value(create_metre(6, 8))
        Fraction(3, 4)

        >>> default_beat_value(create_metre(7, 8))
        Fraction(2, 8)
    """
    if is_compound(metre):
        return create_metre(3, metre.denominator)

    if is_complex(metre):
        return create_metre(2, metre.denominator)

    return create_metre(1, metre.denominator)


def bar_period(tempo, metre=FOUR_FOUR_METRE, beatValue=None):
    """Duration of a single bar for a given tempo."""
    if beatValue is None:
        beatValue = default_beat_value(metre)

    return metre / tempo_2_frequency(tempo) / beatValue


assert bar_period(120) == 2.0
assert bar_period(100) == 2.4
assert bar_period(120, create_metre(3, 4)) == 1.5
assert bar_period(80, create_metre(6, 8)) == 1.5


def angular_velocity(tempo, metre=FOUR_FOUR_METRE, beatValue=None):
    """Calculate angular bar velocity for given tempo in BPM."""
    return TAU / bar_period(tempo, metre, beatValue)
