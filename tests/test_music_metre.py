import unittest

from klang.music.metre import (
    FOUR_FOUR_METRE, THREE_FOUR_METRE, SIX_EIGHT_METRE, create_metre,
    default_beat_value, is_complex, is_compound, is_irrational, is_simple,
    number_of_beats,
    SEVEN_EIGHT_METRE)
from klang.music.note_values import QUARTER_NOTE, DOTTED_QUARTER_NOTE, EIGHT_NOTE


class TestTimeSignatures(unittest.TestCase):
    def test_create_metre_non_normalization(self):
        metre = create_metre(6, 4)

        self.assertEqual(metre.numerator, 6)
        self.assertEqual(metre.denominator, 4)

    def test_is_irrational(self):
        assert not is_irrational(create_metre(3, 4))
        assert is_irrational(create_metre(3, 5))

    def test_is_complex(self):
        assert not is_complex(create_metre(4, 4))
        assert not is_complex(create_metre(3, 4))
        assert not is_complex(create_metre(6, 8))
        assert is_complex(create_metre(5, 4))
        assert is_complex(create_metre(7, 8))

    def test_is_compound(self):
        assert is_compound(create_metre(6, 8))
        assert is_compound(create_metre(9, 8))
        assert is_compound(create_metre(12, 8))
        assert not is_compound(create_metre(3, 4))
        assert not is_compound(create_metre(4, 4))

    def test_is_simple(self):
        assert is_simple(create_metre(4, 4))
        assert is_simple(create_metre(3, 4))
        assert is_simple(create_metre(2, 4))
        assert is_simple(create_metre(3, 8))
        assert is_simple(create_metre(2, 2))
        assert not is_simple(create_metre(6, 8))
        assert not is_simple(create_metre(12, 8))
        assert not is_simple(create_metre(9, 4))


class TestDefaultBeatValue(unittest.TestCase):
    def test_default_beat_value(self):
        twoEights = create_metre(2, 8)

        self.assertEqual(default_beat_value(FOUR_FOUR_METRE), QUARTER_NOTE)
        self.assertEqual(default_beat_value(THREE_FOUR_METRE), QUARTER_NOTE)
        self.assertEqual(default_beat_value(SIX_EIGHT_METRE), DOTTED_QUARTER_NOTE)
        self.assertEqual(default_beat_value(SEVEN_EIGHT_METRE), twoEights)


class TestNumberOfBeats(unittest.TestCase):
    def test_straightforward_examples(self):
        self.assertEqual(number_of_beats(FOUR_FOUR_METRE), 4)
        self.assertEqual(number_of_beats(THREE_FOUR_METRE), 3)
        self.assertEqual(number_of_beats(SIX_EIGHT_METRE), 2)
        self.assertEqual(number_of_beats(SEVEN_EIGHT_METRE), 3.5)

    def test_with_explicit_beat_value(self):
        self.assertEqual(number_of_beats(FOUR_FOUR_METRE, beatValue=EIGHT_NOTE), 8)
        self.assertEqual(number_of_beats(SIX_EIGHT_METRE, beatValue=EIGHT_NOTE), 6)
        self.assertEqual(number_of_beats(SEVEN_EIGHT_METRE, beatValue=EIGHT_NOTE), 7)


if __name__ == '__main__':
    unittest.main()
