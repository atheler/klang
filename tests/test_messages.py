import unittest

from klang.messages import Note


class TestNote(unittest.TestCase):
    def test_json_serialization(self):
        original = Note(pitch=69)
        string = original.to_json()
        duplicate = Note.from_json(string)

        self.assertEqual(original, duplicate)


if __name__ == '__main__':
    unittest.main()
