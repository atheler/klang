import unittest

from klang.arpeggiator import alternate, Arpeggio
from klang.note_effects import NoteLengthener
from klang.connections import MessageInput
from klang.messages import Note


C = Note(pitch=60)
D = Note(pitch=62)
E = Note(pitch=64)
G = Note(pitch=67)
A = Note(pitch=69)


class TestAlternate(unittest.TestCase):
    def test_alternate(self):
        self.assertEqual(alternate(-1, length=5), 2)
        self.assertEqual(alternate(0, length=5), 0)
        self.assertEqual(alternate(1, length=5), 4)
        self.assertEqual(alternate(2, length=5), 1)
        self.assertEqual(alternate(3, length=5), 3)
        self.assertEqual(alternate(4, length=5), 2)
        self.assertEqual(alternate(5, length=5), 0)

        self.assertEqual(alternate(-1, length=4), 2)
        self.assertEqual(alternate(0, length=4), 0)
        self.assertEqual(alternate(1, length=4), 3)
        self.assertEqual(alternate(2, length=4), 1)
        self.assertEqual(alternate(3, length=4), 2)
        self.assertEqual(alternate(4, length=4), 0)


class TestArpeggio(unittest.TestCase):
    def test_up(self):
        arp = Arpeggio(order='up', initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), C)

    def test_down(self):
        arp = Arpeggio(order='down', initialNotes=[C, E, G])

        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), G)

    def test_random(self):
        triad = [C, E, G]
        arp = Arpeggio(order='down', initialNotes=triad)

        self.assertIn(next(arp), triad)
        self.assertIn(next(arp), triad)
        self.assertIn(next(arp), triad)
        self.assertIn(next(arp), triad)
        self.assertIn(next(arp), triad)
        self.assertIn(next(arp), triad)

    def test_up_down(self):
        arp = Arpeggio(order='upDown', initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), C)

    def test_down_up(self):
        arp = Arpeggio(order='downUp', initialNotes=[C, E, G])

        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)
        self.assertEqual(next(arp), G)

    def test_alternating(self):
        # With 4 notes
        arp = Arpeggio(order='alternating', initialNotes=[C, D, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), D)
        self.assertEqual(next(arp), E)

        # With 5 notes
        arp = Arpeggio(order='alternating', initialNotes=[C, D, E, G, A])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), A)
        self.assertEqual(next(arp), D)
        self.assertEqual(next(arp), G)
        self.assertEqual(next(arp), E)

    def test_removing_played_note(self):
        arp = Arpeggio(initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)

        arp.remove_note(E._replace(velocity=0.))

        self.assertEqual(next(arp), G)

    def test_removing_unplayed_note(self):
        arp = Arpeggio(initialNotes=[C, E, G])

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)

        arp.remove_note(G._replace(velocity=0.))

        self.assertEqual(next(arp), C)
        self.assertEqual(next(arp), E)


class TestableNoteLengthener(NoteLengthener):
    def __init__(self, duration=2):
        super().__init__(duration)
        self.currentTime = 0.

    def clock(self):
        return self.currentTime


class TestNoteLengthener(unittest.TestCase):
    def test_scenario(self):
        nl = TestableNoteLengthener(duration=2)
        recv = MessageInput()
        nl.output.connect(recv)
        nl.input.push(C)  # Add first note at time 0.
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (2, C),
        ])

        nl.currentTime = 1
        nl.input.push(E)  # Add second note at time 1.
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (2, C),
            (3, E),
        ])

        nl.currentTime = 2
        nl.update()

        self.assertEqual(list(nl.activeNotes), [
            (3, E),
        ])
        self.assertEqual(recv.receive_latest(), C._replace(velocity=0.))


if __name__ == '__main__':
    unittest.main()
