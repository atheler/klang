import unittest

from klang.arpeggiator import Arpeggio
from klang.messages import Note


C = Note(pitch=60)
D = Note(pitch=62)
E = Note(pitch=64)
G = Note(pitch=67)
A = Note(pitch=69)


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


if __name__ == '__main__':
    unittest.main()
