import fractions

from klang.music.metre import FOUR_FOUR, is_compound, create_metre


def tempo_2_frequency(tempo):
    """Convert beats per minute (BPM) to frequency."""
    return tempo / 60.


def estimate_beat_value(metre):
    """Get note value of a single beat from metre.

    Example:
      - 4/4 -> 1/4
      - 3/4 -> 1/4
      - 6/8 -> 3/8
    """
    if is_compound(metre):
        return fractions.Fraction(3, metre.denominator)

    return fractions.Fraction(1, metre.denominator)


def bar_period(tempo, metre=FOUR_FOUR):
    """Duration of a single bar for a given tempo."""
    beatValue = estimate_beat_value(metre)
    return metre / tempo_2_frequency(tempo) / beatValue


assert bar_period(120) == 2.0
assert bar_period(100) == 2.4
assert bar_period(120, create_metre(3, 4)) == 1.5
assert bar_period(80, create_metre(6, 8)) == 1.5
