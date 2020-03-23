import unittest

from klang.audio.synthesizer import NoteScheduler
from klang.messages import Note
from klang.music.tunings import EQUAL_TEMPERAMENT


def make_notes(*pitches, velocity=1., temperament=EQUAL_TEMPERAMENT):
    """Make notes from pitches."""
    return [
        Note(pitch=pitch, velocity=velocity) for pitch in pitches
    ]


C_MAJOR_CHORD = [60, 64, 67]
C_ON, E_ON, G_ON = make_notes(*C_MAJOR_CHORD)
C_OFF, E_OFF, G_OFF = make_notes(*C_MAJOR_CHORD, velocity=0.)
DOUBLE_RISING = [C_ON, E_ON, G_ON, C_OFF, E_OFF, G_OFF]
RISE_AND_FALL = [C_ON, E_ON, G_ON, G_OFF, E_OFF, C_OFF]
DOUBLE_FALLING = [G_ON, E_ON, C_ON, G_OFF, E_OFF, C_OFF]
FALL_AND_RISE = [G_ON, E_ON, C_ON, C_OFF, E_OFF, G_OFF]


class TestNoteScheduler(unittest.TestCase):
    def assert_fits(self, scheduler, notes, expected):
        for note, soll in zip(notes, expected):
            self.assertEqual(scheduler.get_next_note(note), soll)

    def test_newest_policy(self):
        scheduler = NoteScheduler(policy='newest')

        self.assert_fits(scheduler, DOUBLE_RISING, [C_ON, E_ON, G_ON, G_ON, G_ON, G_OFF])
        self.assert_fits(scheduler, RISE_AND_FALL, [C_ON, E_ON, G_ON, E_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, DOUBLE_FALLING, [G_ON, E_ON, C_ON, C_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, FALL_AND_RISE, [G_ON, E_ON, C_ON, E_ON, G_ON, G_OFF])

    def test_oldest_policy(self):
        scheduler = NoteScheduler(policy='oldest')

        self.assert_fits(scheduler, DOUBLE_RISING, [C_ON, C_ON, C_ON, E_ON, G_ON, G_OFF])
        self.assert_fits(scheduler, RISE_AND_FALL, [C_ON, C_ON, C_ON, C_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, DOUBLE_FALLING, [G_ON, G_ON, G_ON, E_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, FALL_AND_RISE, [G_ON, G_ON, G_ON, G_ON, G_ON, G_OFF])

    def test_lowest_policy(self):
        scheduler = NoteScheduler(policy='lowest')

        self.assert_fits(scheduler, DOUBLE_RISING, [C_ON, C_ON, C_ON, E_ON, G_ON, G_OFF])
        self.assert_fits(scheduler, RISE_AND_FALL, [C_ON, C_ON, C_ON, C_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, DOUBLE_FALLING, [G_ON, E_ON, C_ON, C_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, FALL_AND_RISE, [G_ON, E_ON, C_ON, E_ON, G_ON, G_OFF])

    def test_highest_policy(self):
        scheduler = NoteScheduler(policy='highest')

        self.assert_fits(scheduler, DOUBLE_RISING, [C_ON, E_ON, G_ON, G_ON, G_ON, G_OFF])
        self.assert_fits(scheduler, RISE_AND_FALL, [C_ON, E_ON, G_ON, E_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, DOUBLE_FALLING, [G_ON, G_ON, G_ON, E_ON, C_ON, C_OFF])
        self.assert_fits(scheduler, FALL_AND_RISE, [G_ON, G_ON, G_ON, G_ON, G_ON, G_OFF ])

    def test_release(self):
        scheduler = NoteScheduler()

        self.assertEqual(scheduler.get_next_note(C_ON), C_ON)
        self.assertEqual(scheduler.get_next_note(C_OFF), C_OFF)


if __name__ == '__main__':
    unittest.main()
