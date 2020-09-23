import unittest

from klang.block import fetch_output, fetch_input, Block
from klang.audio.mixer import Mixer
from klang.connections import IncompatibleConnection


class TestOperatorOverloading(unittest.TestCase):
    def assert_is_connected(self, a, b):
        """Assert that a is connected with b (directional)."""
        output = fetch_output(a)
        input_ = fetch_input(b)
        self.assertIs(output, input_.incomingConnection)
        self.assertIn(input_, output.outgoingConnections)

    def test_mixing(self):
        # __add__(mixer, input)
        with self.assertRaises(IncompatibleConnection):
            Mixer(nInputs=0) + Block(1, 1).input

        # __add__(mixer, output)
        mixer = Mixer(nInputs=0)
        block = Block(1, 1)
        self.assertIs(mixer + block.output, mixer)
        self.assert_is_connected(block, mixer.inputs[0])

        # __add__(mixer, block), no output
        with self.assertRaises(AttributeError):
            Mixer(nInputs=0) + Block()

        # __add__(mixer, block)
        mixer = Mixer(nInputs=0)
        block = Block(1, 1)
        self.assertIs(mixer + block, mixer)
        self.assert_is_connected(block, mixer.inputs[0])

        # __radd__(input, mixer)
        with self.assertRaises(IncompatibleConnection):
            Block(1, 1).input + Mixer(nInputs=0)

        # __radd__(output, mixer)
        mixer = Mixer(nInputs=0)
        block = Block(1, 1)
        self.assertIs(block.output + mixer, mixer)
        self.assert_is_connected(block, mixer.inputs[0])

        # __radd__(block, mixer), no output
        with self.assertRaises(AttributeError):
            Block() + Mixer(nInputs=0)

        # __radd__(block, mixer)
        mixer = Mixer(nInputs=0)
        block = Block(1, 1)
        self.assertIs(block + mixer, mixer)
        self.assert_is_connected(block, mixer.inputs[0])


if __name__ == '__main__':
    unittest.main()
