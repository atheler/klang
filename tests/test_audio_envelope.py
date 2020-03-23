import unittest
import collections

from klang.audio.envelope import EnvelopeGenerator
from klang.messages import Note


Scenario = collections.namedtuple('Scenario', 'initialState notes shouldBeDirty shouldBeTriggered')
ON = Note(pitch=69, velocity=1.)
OFF = Note(pitch=69, velocity=0.)


class TestEnvelopeGenerator(unittest.TestCase):
    DIRTY_SCENARIOS = [
        # Single note
        Scenario(initialState=False, notes=[OFF], shouldBeDirty=False, shouldBeTriggered=False),
        Scenario(initialState=False, notes=[ON], shouldBeDirty=True, shouldBeTriggered=True),
        Scenario(initialState=True, notes=[OFF], shouldBeDirty=True, shouldBeTriggered=False),
        Scenario(initialState=True, notes=[ON], shouldBeDirty=False, shouldBeTriggered=True),

        # Multiple notes
        Scenario(initialState=False, notes=[OFF, OFF], shouldBeDirty=False, shouldBeTriggered=False),
        Scenario(initialState=False, notes=[OFF, ON], shouldBeDirty=True, shouldBeTriggered=True),
        Scenario(initialState=False, notes=[ON, OFF], shouldBeDirty=False, shouldBeTriggered=False),
        Scenario(initialState=False, notes=[ON, ON], shouldBeDirty=True, shouldBeTriggered=True),
        Scenario(initialState=True, notes=[OFF, OFF], shouldBeDirty=True, shouldBeTriggered=False),
        Scenario(initialState=True, notes=[OFF, ON], shouldBeDirty=False, shouldBeTriggered=True),
        Scenario(initialState=True, notes=[ON, OFF], shouldBeDirty=True, shouldBeTriggered=False),
        Scenario(initialState=True, notes=[ON, ON], shouldBeDirty=False, shouldBeTriggered=True),
    ]

    def run_scenario(self, scenario):
            env = EnvelopeGenerator()
            env.triggered = scenario.initialState
            for note in scenario.notes:
                env.input.push(note)

            self.assertEqual(env.dirty(), scenario.shouldBeDirty)
            self.assertFalse(env.dirty())
            self.assertEqual(env.triggered, scenario.shouldBeTriggered)

    def test_dirty_logic(self):
        for scenario in self.DIRTY_SCENARIOS:
            self.run_scenario(scenario)


if __name__ == '__main__':
    unittest.main()
