import unittest

from klang.messages import Note


class TestNote(unittest.TestCase):
    def test_json_serialization(self):
        original = Note(pitch=69)
        string = original.to_json()
        duplicate = Note.from_json(string)

        self.assertEqual(original, duplicate)

    def test_dict_conversion(self):
        c = Note(pitch=60)
        dct = c.to_dict()

        self.assertEqual(dct['pitch'], 60)
        self.assertEqual(dct['velocity'], 1.)
        self.assertEqual(dct['type'], 'Note')

        self.assertEqual(c, Note.from_dict(dct))


if __name__ == '__main__':
    unittest.main()
