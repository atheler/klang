import unittest

from klang.music.metre import (
    create_metre, is_irrational, is_complex, is_compound, is_simple
)


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


if __name__ == '__main__':
    unittest.main()
