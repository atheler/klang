"""Tempo of music."""
import fractions

from klang.config import TEMPO, METRE
from klang.constants import TAU
from klang.music.metre import default_beat_value


def tempo_2_frequency(tempo):
    """Convert beats per minute (BPM) to beat frequency.

    Args:
        tempo (float): Beats per minute.

    Returns:
        float: Frequency.
    """
    minute = 60.
    return tempo / minute


def tempo_2_period(tempo):
    """Convert beats per minute (BPM) to beat period.

    Args:
        tempo (float): Beats per minute.

    Returns:
        float: Period.
    """
    return 1. / tempo_2_frequency(tempo)


def bar_period(tempo, metre=METRE, beatValue=None):
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


def angular_velocity(tempo, metre=METRE, beatValue=None):
    """Calculate angular bar velocity for given tempo in BPM."""
    return TAU / bar_period(tempo, metre, beatValue)


def note_duration(note, tempo=TEMPO, metre=METRE, beatValue=None):
    """Note duration relative to tempo, metre or beat value.

    Args:
        note (Fraction): Note value.

    Kwargs:
        tempo (float): Beats per minute.
        metre (Fraction): Time signature.
        beatValue (Fraction): Note beat value.

    Returns:
        float: Note duration relative to tempo / beat value.
    """
    if beatValue is None:
        beatValue = default_beat_value(metre)

    beatFrequency = tempo_2_frequency(tempo)
    beatPeriod = 1. / beatFrequency
    return beatPeriod / beatValue * note


def compute_duration(duration, *args, **kwargs):
    """Tempo aware duration."""
    if isinstance(duration, fractions.Fraction):
        return note_duration(duration, *args, **kwargs)

    return duration


def compute_rate(rate, *args, **kwargs):
    """Tempo aware rate. Convert note value to frequency (relative to tempo and
    beat value). Pass through float.
    """
    if isinstance(rate, fractions.Fraction):
        return 1. / note_duration(rate, *args, **kwargs)

    return rate
