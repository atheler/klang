"""Music intervals.

Resources:
  - http://huygens-fokker.org/docs/intervals.html
"""
import fractions
import os

from klang.config import INTERVALS_FILEPATH
from klang import ROOT_DIR
from klang.util import find_item
from klang.util import load_music_data_from_csv


INTERVALS = {}
"""dict: Interval name (str) -> Chord (Fraction)."""


def find_interval(name):
    """Find interval by name."""
    return find_item(INTERVALS, name)


def _load_intervals_from_csv(filepath):
    """Load intervals from CSV file."""
    intervals = {
        name: fractions.Fraction(ratio[0])
        for name, ratio in load_music_data_from_csv(filepath).items()
    }
    return intervals


INTERVALS = _load_intervals_from_csv(
    os.path.join(ROOT_DIR, INTERVALS_FILEPATH)
)
