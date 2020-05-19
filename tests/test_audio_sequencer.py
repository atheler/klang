import unittest
import collections

from klang.block import Block
from klang.connections import MessageInput

from klang.sequencer import PizzaSlicer
from klang.constants import TAU


class Receiver(Block):
    def __init__(self):
        super().__init__()
        self.inputs = [MessageInput(owner=self)]


class TestPizzaSlicer(unittest.TestCase):
    def setUp(self):
        self.receiver = Receiver()

    def compare_messages(self, messages=None):
        if not messages:
            return self.assertEqual(len(self.receiver.input.queue), 0)

        for received, msg in zip(self.receiver.input.receive(), messages):
            self.assertEqual(received, msg)

    def test_start_index(self):
        pizza = PizzaSlicer(16)
        pizza.output.connect(self.receiver.input)

        self.assertEqual(pizza.currentIdx, -1)

        pizza.update()

        self.assertEqual(pizza.currentIdx, 0)
        self.compare_messages([0])

    def test_pattern_of_four(self):
        pizza = PizzaSlicer(4)
        pizza.output.connect(self.receiver.input)
        cases = [
            (.0 * TAU, [0]),
            (.25 * TAU - .1, None),
            (.25 * TAU, [1]),
            (.25 * TAU + .1, None),
            (.50 * TAU, [2]),
            (.75 * TAU, [3]),
            (1.0 * TAU - .1, None),
            (1.0 * TAU + .1, [0]),
        ]
        for phase, messages in cases:
            pizza.input.set_value(0.)
            pizza.update()
            self.compare_messages(messages)

    def test_double_jump(self):
        """Multiple pizza slice jumps at once."""

        pizza = PizzaSlicer(4)
        pizza.output.connect(self.receiver.input)
        cases = [
            (.0 * TAU, [0]),
            (.50 * TAU, [1, 2]),
            (1.0 * TAU, [3, 0]),
        ]
        for phase, messages in cases:
            pizza.input.set_value(0.)
            pizza.update()
            self.compare_messages(messages)


if __name__ == '__main__':
    unittest.main()
