import unittest

from klang.block import Block
from klang.audio.mixer import Mixer


class TestBlock(unittest.TestCase):
    def assert_is_connected(self, a, b):
        self.assertIs(a.output, b.input.incomingConnection)
        self.assertIn(b.input, a.output.outgoingConnections)

    def test_operator_or(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        d = a | b | c

        self.assertIs(d, c)
        self.assert_is_connected(a, b)
        self.assert_is_connected(b, c)

    def test_operator_and(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        mixer = a + b + c

        self.assertIs(type(mixer), Mixer)

        self.assertIs(a.output, mixer.inputs[0].incomingConnection)
        self.assertIn(mixer.inputs[0], a.output.outgoingConnections)

        self.assertIs(b.output, mixer.inputs[1].incomingConnection)
        self.assertIn(mixer.inputs[1], b.output.outgoingConnections)

        self.assertIs(c.output, mixer.inputs[2].incomingConnection)
        self.assertIn(mixer.inputs[2], c.output.outgoingConnections)


if __name__ == '__main__':
    unittest.main()
