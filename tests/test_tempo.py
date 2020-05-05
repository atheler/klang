import unittest

from klang.music.metre import FOUR_FOUR_METRE, create_metre
from klang.music.note_values import EIGHT_NOTE, QUARTER_NOTE, HALF_NOTE, WHOLE_NOTE
from klang.music.tempo import note_duration, bar_period


class TestTempo(unittest.TestCase):

    """Test helper functions in tempo module."""

    def test_bar_period(self):
        """Test bar_period() function."""
        self.assertEqual(bar_period(120), 2.0)
        self.assertEqual(bar_period(100), 2.4)
        self.assertEqual(bar_period(120, create_metre(3, 4)), 1.5)
        self.assertEqual(bar_period(80, create_metre(6, 8)), 1.5)

    def test_note_duration(self):
        """Test note_duration() function."""
        self.assertEqual(note_duration(EIGHT_NOTE, 120, FOUR_FOUR_METRE), .25)
        self.assertEqual(note_duration(QUARTER_NOTE, 120, FOUR_FOUR_METRE), .5)
        self.assertEqual(note_duration(HALF_NOTE, 120, FOUR_FOUR_METRE), 1.)
        self.assertEqual(note_duration(WHOLE_NOTE, 120, FOUR_FOUR_METRE), 2.)


if __name__ == '__main__':
    unittest.main()
