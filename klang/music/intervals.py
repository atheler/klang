"""Music intervals.

Resources:
  - http://huygens-fokker.org/docs/intervals.html
"""
import fractions
import pkgutil

from klang.util import find_item
from klang.util import parse_music_data_from_csv


__all__ = ['INTERVALS', 'find_interval']


INTERVALS = {}
"""dict: Interval name (str) -> Chord (Fraction)."""


def find_interval(name):
    """Find interval by name."""
    return find_item(INTERVALS, name)


def _load_intervals():
    """Load intervals from CSV file."""
    data = pkgutil.get_data('klang.music', 'data/intervals.csv')
    intervals = {
        name: fractions.Fraction(ratio[0])
        for name, ratio in parse_music_data_from_csv(data).items()
    }

    return intervals


INTERVALS = _load_intervals()