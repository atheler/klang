"""Tempo of music."""
from klang.constants import TAU
from klang.music.metre import (
    FOUR_FOUR_METRE,
    create_metre,
    default_beat_value,
)


def tempo_2_frequency(tempo):
    """Convert beats per minute (BPM) to frequency.

    Args:
        tempo (float): Beats per minute.

    Returns:
        float: Frequency.
    """
    minute = 60.
    return tempo / minute


def bar_period(tempo, metre=FOUR_FOUR_METRE, beatValue=None):
    """Duration of a single bar for a given tempo.

    Args:
        tempo (float): Beats per minute.

    Kwargs:
        metre (Fraction): Time signature.
        beatValue (Fraction): Beat value.

    Returns:
        float: Bar duration in seconds.
    """
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
