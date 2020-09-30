"""Test note name to pitch conversion."""
import unittest

from klang.music.pitch import note_name_2_pitch, pitch_2_note_name


class TestNoteNamePitchConversion(unittest.TestCase):
    def test_omitting_number_leads_to_value_error(self):
        with self.assertRaises(ValueError):
            note_name_2_pitch('C#')

    def test_invalid_note_letter_leads_to_value_error(self):
        notANote = 'q4'
        with self.assertRaises(ValueError):
            note_name_2_pitch(notANote)

    def test_upper_and_lower_case_leads_to_the_same_results(self):
        for name in ['c4', 'd4', 'e4', 'f4', 'g4', 'a4', 'b4']:
            self.assertEqual(
                note_name_2_pitch(name.upper()), note_name_2_pitch(name.lower())
            )

    def test_double_sharp_leads_to_one_whole_note(self):
        self.assertEqual(note_name_2_pitch('G##4'), note_name_2_pitch('G4') + 2)

    def test_double_b_decreases_by_one_whole_note(self):
        self.assertEqual(note_name_2_pitch('Gbb4'), note_name_2_pitch('G4') - 2)

    def test_there_is_no_triple_accident(self):
        with self.assertRaises(ValueError):
            note_name_2_pitch('C###4')

        with self.assertRaises(ValueError):
            note_name_2_pitch('Cbbb4')

    def test_proper_results_with_reference_values(self):
        self.assertEqual(note_name_2_pitch('C4'), 60)
        self.assertEqual(note_name_2_pitch('C#4'), 61)
        self.assertEqual(note_name_2_pitch('Db4'), 61)
        self.assertEqual(note_name_2_pitch('D4'), 62)
        self.assertEqual(note_name_2_pitch('D#4'), 63)
        self.assertEqual(note_name_2_pitch('Eb4'), 63)
        self.assertEqual(note_name_2_pitch('E4'), 64)
        self.assertEqual(note_name_2_pitch('F4'), 65)
        self.assertEqual(note_name_2_pitch('F#4'), 66)
        self.assertEqual(note_name_2_pitch('Gb4'), 66)
        self.assertEqual(note_name_2_pitch('G4'), 67)
        self.assertEqual(note_name_2_pitch('G#4'), 68)
        self.assertEqual(note_name_2_pitch('Ab4'), 68)
        self.assertEqual(note_name_2_pitch('A4'), 69)
        self.assertEqual(note_name_2_pitch('A#4'), 70)
        self.assertEqual(note_name_2_pitch('Bb4'), 70)
        self.assertEqual(note_name_2_pitch('B4'), 71)
        self.assertEqual(note_name_2_pitch('C5'), 72)

    def test_with_minus_sign(self):
        self.assertEqual(note_name_2_pitch('c-1'), 0)
        self.assertEqual(note_name_2_pitch('c#-1'), 1)

    def test_back_mapping_to_sharp_notes(self):
        sharpNotes = [
            'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4',
            'A#4', 'B4', 'C5',
        ]

        for name in sharpNotes:
            pitch = note_name_2_pitch(name)
            result = pitch_2_note_name(pitch)
            self.assertEqual(result, name)


if __name__ == '__main__':
    unittest.main()
