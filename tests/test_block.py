"""Test Block class."""
import unittest

from klang.audio.mixer import Mixer
from klang.block import fetch_output, fetch_input, Block
from klang.connections import IncompatibleConnection


class TestPipeingOperator(unittest.TestCase):
    def assert_is_connected(self, a, b):
        """Assert that a is connected with b (directional)."""
        output = fetch_output(a)
        input_ = fetch_input(b)
        self.assertIs(output, input_.incomingConnection)
        self.assertIn(input_, output.outgoingConnections)

    def test_pipeing_between_blocks(self):
        # __or__(block, block), no output, no input
        with self.assertRaises(AttributeError):
            Block() | Block()

        # __or__(block, block), no input
        with self.assertRaises(AttributeError):
            Block(0, 1) | Block()

        # __or__(block, block), no output
        with self.assertRaises(AttributeError):
            Block() | Block(1, 0)

        # __or__(block, block)
        a = Block(0, 1)
        b = Block(1, 0)
        self.assertIs(a | b, b)
        self.assert_is_connected(a, b)

    def test_pipeing_between_blocks_and_connections(self):
        # __or__(block, input)
        a = Block(1, 1)
        b = Block(1, 1)
        self.assertIs(a | b.input, b)
        self.assert_is_connected(a, b)

        # __or__(block, output)
        with self.assertRaises(TypeError):
            Block(1, 1) | Block(1, 1).output

        # __ror__(input, block)
        with self.assertRaises(TypeError):
            Block(1, 1).input | Block(1, 1)

        # __ror__(output, block)
        a = Block(1, 1)
        b = Block(1, 1)
        self.assertIs(a.output | b, b)
        self.assert_is_connected(a, b)


class TestMixOperator(unittest.TestCase):
    def assert_is_connected(self, a, b):
        """Assert that a is connected with b (directional)."""
        output = fetch_output(a)
        input_ = fetch_input(b)
        self.assertIs(output, input_.incomingConnection)
        self.assertIn(input_, output.outgoingConnections)

    def test_mixing_between_blocks(self):
        # __add__(block, block), no output, no input
        with self.assertRaises(AttributeError):
            Block() + Block()

        # __add__(block, block), no input
        with self.assertRaises(AttributeError):
            Block(0, 1) + Block()

        # __add__(block, block), no output
        with self.assertRaises(AttributeError):
            Block() + Block(0, 1)

        # __add__(block, block) and chain of three
        a = Block(0, 1)
        b = Block(0, 1)
        c = Block(0, 1)
        mixer = a + b + c
        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])
        self.assert_is_connected(c, mixer.inputs[2])

    def test_mixing_between_blocks_and_connections(self):
        # __add__(block, input)
        with self.assertRaises(AttributeError):
            Block(0, 1) + Block(0, 1).input

        # __add__(block, output)
        a = Block(0, 1)
        b = Block(0, 1)
        mixer = a + b.output
        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])

        # __radd__(input, block)
        with self.assertRaises(TypeError):
            Block(1, 1).input + Block(1, 1)

        # __radd__(output, block) and chain of three
        a = Block(0, 1)
        b = Block(0, 1)
        c = Block(0, 1)
        mixer = a.output + b + c.output
        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])
        self.assert_is_connected(c, mixer.inputs[2])


if __name__ == '__main__':
    unittest.main()
