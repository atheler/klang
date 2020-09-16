"""Music intervals.

Resources:
  - http://huygens-fokker.org/docs/intervals.html
"""
from typing import Dict
from fractions import Fraction
import pkgutil

from klang.util import find_item
from klang.util import parse_music_data_from_csv


__all__ = ['INTERVALS', 'find_interval']


INTERVALS: Dict[str, Fraction] = {}
"""Interval name to chord mapping."""


def find_interval(name: str) -> Fraction:
    """Find interval by name."""
    return find_item(INTERVALS, name)


def _load_intervals() -> Dict:
    """Load intervals from CSV file."""
    data = pkgutil.get_data('klang.music', 'data/intervals.csv')
    intervals = {
        name: Fraction(ratio[0])
        for name, ratio in parse_music_data_from_csv(data).items()
    }

    return intervals


INTERVALS = _load_intervals()
