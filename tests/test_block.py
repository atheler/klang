"""Test Block class."""
import unittest

from klang.block import Block
from klang.audio.mixer import Mixer


class TestOperatorOverloading(unittest.TestCase):
    def assert_is_connected(self, a, b):
        """Assert that a is connected with b (directional)."""
        if isinstance(a, Block):
            output = a.output
        else:
            output = a

        if isinstance(b, Block):
            input_ = b.input
        else:
            input_ = b

        self.assertIs(output, input_.incomingConnection)
        self.assertIn(input_, output.outgoingConnections)

    def test_piping_muliple_blocks(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        d = a | b | c

        self.assertIs(d, c)
        self.assert_is_connected(a, b)
        self.assert_is_connected(b, c)

    def test_adding_multiple_blocks(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        mixer = a + b + c

        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])
        self.assert_is_connected(c, mixer.inputs[2])

    def test_piping_with_connections(self):
        a = Block(nOutputs=1)
        b = Block(nInputs=1)

        self.assertIs(a | b.input, b)
        self.assert_is_connected(a, b)

    def test_adding_with_connections(self):
        a = Block(nOutputs=1)
        b = Block(nOutputs=1)

        mixer = a + b.output
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])


if __name__ == '__main__':
    unittest.main()
