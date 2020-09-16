"""Tempo of music."""
from fractions import Fraction
from typing import Union

from klang.config import TEMPO, METRE
from klang.constants import TAU
from klang.music.metre import default_beat_value


__all__ = [
    'TimeOrNoteValue', 'tempo_2_frequency', 'tempo_2_period', 'bar_period',
    'angular_velocity', 'note_duration', 'compute_duration', 'compute_rate'
]


TimeOrNoteValue = Union[float, Fraction]


def tempo_2_frequency(tempo: float) -> float:
    """Convert beats per minute (BPM) to beat frequency.

    Args:
        tempo: Beats per minute.

    Returns:
        Frequency value.
    """
    minute = 60.
    return tempo / minute


def tempo_2_period(tempo: float) -> float:
    """Convert beats per minute (BPM) to beat period.

    Args:
        tempo: Beats per minute.

    Returns:
        Period duration.
    """
    return 1. / tempo_2_frequency(tempo)


def bar_period(tempo: float, metre: Fraction = METRE,
               beatValue: Fraction = None) -> float:
    """Duration of a single bar for a given tempo.

    Args:
        tempo: Beats per minute.

    Kwargs:
        metre: Time signature.
        beatValue: Beat value.

    Returns:
        Bar duration in seconds.
    """
    if beatValue is None:
        beatValue = default_beat_value(metre)

    return metre / tempo_2_frequency(tempo) / beatValue


def angular_velocity(tempo: float, metre: Fraction = METRE,
                     beatValue: Fraction = None) -> float:
    """Calculate angular bar velocity for given tempo in BPM."""
    return TAU / bar_period(tempo, metre, beatValue)


def note_duration(note: Fraction, tempo: float = TEMPO, metre: Fraction = METRE,
                  beatValue: Fraction = None) -> float:
    """Note duration relative to tempo, metre or beat value.

    Args:
        note: Note value.

    Kwargs:
        tempo: Beats per minute.
        metre: Time signature.
        beatValue: Note beat value.

    Returns:
        Note duration relative to tempo / beat value.
    """
    if beatValue is None:
        beatValue = default_beat_value(metre)

    beatFrequency = tempo_2_frequency(tempo)
    beatPeriod = 1. / beatFrequency
    return beatPeriod / beatValue * note


def compute_duration(duration: TimeOrNoteValue, *args, **kwargs) -> float:
    """Tempo aware duration."""
    if isinstance(duration, Fraction):
        return note_duration(duration, *args, **kwargs)

    return duration


def compute_rate(frequency: TimeOrNoteValue, *args, **kwargs) -> float:
    """Tempo aware frequency. Convert note value to frequency (relative to tempo
    and beat value). Pass through float.
    """
    if isinstance(frequency, Fraction):
        return 1. / note_duration(frequency, *args, **kwargs)

    return frequency
