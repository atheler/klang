"""Music intervals.

Resources:
  - http://huygens-fokker.org/docs/intervals.html
"""
import fractions

from config import INTERVALS_FILEPATH
from klang.util import find_item
from klang.util import load_music_data_from_csv


INTERVALS = {
    name: fractions.Fraction(ratio[0])
    for name, ratio in load_music_data_from_csv(INTERVALS_FILEPATH).items()
}


def find_interval(name):
    """Find interval by name."""
    return find_item(INTERVALS, name)
