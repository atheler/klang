import unittest
import itertools

from klang.arpeggiator import (
    Arpeggio,
    interleave,
    VALID_ORDERS,
    arpeggio_index_permutation,
)
from klang.note_effects import NoteLengthener
from klang.connections import MessageInput
from klang.messages import Note


C = Note(60)
D = Note(62)
E = Note(64)
F = Note(65)
G = Note(67)
A = Note(69)
B = Note(71)


def grab_next_notes(arpeggio, nNotes):
    """Grab next n notes from arpeggio as a list."""
    return [
        next(arpeggio) for _ in range(nNotes)
    ]


class TestInterleave(unittest.TestCase):
    def test_with_argument_cases(self):
        self.assertEqual(interleave('ab', '01'), ['a', '0', 'b', '1'])
        self.assertEqual(interleave('abc', '01'), ['a', '0', 'b', '1', 'c'])
        self.assertEqual(interleave('abcde', '01'), ['a', '0', 'b', '1', 'c', 'd', 'e'])
        self.assertEqual(interleave('ab', '0123'), ['a', '0', 'b', '1', '2', '3'])


class TestArpeggioIndexPermutation(unittest.TestCase):
    def test_invalid_order_raises_value_error(self):
        with self.assertRaises(ValueError):
            arpeggio_index_permutation('notAValidOrder', 2)

    def test_zero_length_returns_empty_permutation(self):
        for order in VALID_ORDERS:
            permut = arpeggio_index_permutation(order, 0)
            self.assertEqual(permut, [])

    def test_with_length_one(self):
        self.assertEqual(arpeggio_index_permutation('up', 1), [0])
        self.assertEqual(arpeggio_index_permutation('down', 1), [0])
        self.assertEqual(arpeggio_index_permutation('upDown', 1), [0])
        self.assertEqual(arpeggio_index_permutation('downUp', 1), [0])
        self.assertEqual(arpeggio_index_permutation('alternating', 1), [0])

    def test_with_even_lengths(self):
        self.assertEqual(arpeggio_index_permutation('up', 4), [0, 1, 2, 3])
        self.assertEqual(arpeggio_index_permutation('down', 4), [3, 2, 1, 0])
        self.assertEqual(arpeggio_index_permutation('upDown', 4), [0, 1, 2, 3, 2, 1])
        self.assertEqual(arpeggio_index_permutation('downUp', 4), [3, 2, 1, 0, 1, 2])
        self.assertEqual(arpeggio_index_permutation('alternating', 4), [0, 3, 1, 2])

    def test_with_uneven_lengths(self):
        self.assertEqual(arpeggio_index_permutation('up', 3), [0, 1, 2])
        self.assertEqual(arpeggio_index_permutation('down', 3), [2, 1, 0])
        self.assertEqual(arpeggio_index_permutation('upDown', 3), [0, 1, 2, 1])
        self.assertEqual(arpeggio_index_permutation('downUp', 3), [2, 1, 0, 1])
        self.assertEqual(arpeggio_index_permutation('alternating', 3), [0, 2, 1])


class TestArpeggio(unittest.TestCase):
    def test_empty_arpeggio_raises_StopIteration(self):
        arp = Arpeggio()
        with self.assertRaises(StopIteration):
            next(arp)

    def test_single_note_arpeggio_always_gives_the_same_note(self):
        for order in VALID_ORDERS:
            arp = Arpeggio(order, initialNotes=[C])
            for _ in range(10):
                self.assertEqual(next(arp), C)

    def test_raises_ValueError_when_note_is_not_in_arpeggio(self):
        arp = Arpeggio()
        with self.assertRaises(ValueError):
            arp.remove_note(C)

    def test_empty_state_when_removing_all_notes(self):
        notes = [C, E, G]
        arp = Arpeggio(initialNotes=notes)
        for note in notes:
            arp.remove_note(note)

        self.assertEqual(arp.current, 0)
        self.assertEqual(arp.permutation, [])

    def test_three_note_up_arpeggio(self):
        arp = Arpeggio(order='up', initialNotes=[C, E, G])

        self.assertEqual(grab_next_notes(arp, 4), [C, E, G, C])

    def test_three_note_down_arpeggio(self):
        arp = Arpeggio(order='down', initialNotes=[C, E, G])

        self.assertEqual(grab_next_notes(arp, 4), [G, E, C, G])

    def test_three_note_up_down_arpeggio(self):
        arp = Arpeggio(order='upDown', initialNotes=[C, E, G])

        self.assertEqual(grab_next_notes(arp, 5), [C, E, G, E, C])

    def test_three_note_down_up_arpeggio(self):
        arp = Arpeggio(order='downUp', initialNotes=[C, E, G])

        self.assertEqual(grab_next_notes(arp, 5), [G, E, C, E, G])

    def test_five_note_alternating_arpeggio(self):
        arp = Arpeggio(order='alternating', initialNotes=[A, G, F, D, C])

        self.assertEqual(grab_next_notes(arp, 6), [C, A, D, G, F, C])

    def test_up_arpeggio_keeps_rising_when_adding_a_note_at_the_end(self):
        arp = Arpeggio(order='up', initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)

        arp.add_note(B)

        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), B)

    def test_up_arpeggio_goes_to_first_note_when_removing_the_last(self):
        arp = Arpeggio(order='up', initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)

        arp.remove_note(G)

        self.assertEqual(next(arp), C)


class TestNoteLengthener(unittest.TestCase):
    def test_scenario(self):
        nl = NoteLengthener(duration=2)
        recv = MessageInput()
        nl.output.connect(recv)
        nl.input.push(C)  # Add first note at time 0.
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (2, C),
        ])

        nl.set_current_time(1.)
        nl.input.push(E)  # Add second note at time 1.
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (2, C),
            (3, E),
        ])

        nl.set_current_time(2.)
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (3, E),
        ])
        self.assertEqual(recv.receive_latest(), C._replace(velocity=0.))


if __name__ == '__main__':
    unittest.main()
