import unittest

from klang.config import KAMMERTON
from klang.music.pitch import frequency_2_pitch, pitch_2_frequency, note_name_2_pitch, pitch_2_note_name


class TestMusicPitch(unittest.TestCase):
    def test_frequency_conversion(self):
        self.assertEqual(frequency_2_pitch(KAMMERTON), 69)
        self.assertEqual(pitch_2_frequency(69), KAMMERTON)

    def test_note_name_2_pitch(self):
        self.assertEqual(note_name_2_pitch('c-1'), 0)
        self.assertEqual(note_name_2_pitch('c#-1'), 1)
        self.assertEqual(note_name_2_pitch('Cb0'), 11)
        self.assertEqual(note_name_2_pitch('B0'), 23)
        self.assertEqual(note_name_2_pitch('a4'), 69)
        self.assertEqual(note_name_2_pitch('G##4'), 69)
        self.assertEqual(note_name_2_pitch('A4'), note_name_2_pitch('A5', midi=True))

        self.assertEqual(note_name_2_pitch(pitch_2_note_name(69)), 69)
        self.assertEqual(note_name_2_pitch(pitch_2_note_name(69, midi=True), midi=True), 69)


if __name__ == '__main__':
    unittest.main()
