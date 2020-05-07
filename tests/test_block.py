"""Test Block class."""
import unittest

from klang.audio.mixer import Mixer
from klang.block import Block
from klang.connections import IncompatibleError


class TestPipeing(unittest.TestCase):
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

    def test_pipeing_between_blocks(self):
        with self.assertRaises(AttributeError):
            Block() | Block()

        with self.assertRaises(AttributeError):
            Block(0, 1) | Block()

        with self.assertRaises(AttributeError):
            Block() | Block(1, 0)

        a = Block(0, 1)
        b = Block(1, 0)
        c = a | b

        self.assertIs(c, b)
        self.assert_is_connected(a, b)

    def test_pipeing_between_blocks_and_connections(self):
        with self.assertRaises(IncompatibleError):
            Block(1, 1) | Block(1, 1).output

        a = Block(1, 1)
        b = Block(1, 1)
        c = a.output | b

        self.assertIs(c, b)
        self.assert_is_connected(a, b)

        with self.assertRaises(TypeError):
            Block(1, 1).input | Block(1, 1)

        a = Block(1, 1)
        b = Block(1, 1)
        c = a | b.input

        self.assertIs(c, b)
        self.assert_is_connected(a, b)


class TestMixing(unittest.TestCase):
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

    def test_mixing_between_blocks(self):
        with self.assertRaises(AttributeError):
            Block() + Block()

        with self.assertRaises(AttributeError):
            Block(0, 1) + Block()

        with self.assertRaises(AttributeError):
            Block() + Block(0, 1)

        a = Block(0, 1)
        b = Block(0, 1)
        mixer = a + b

        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])

    def test_mixing_between_blocks_and_connections(self):
        a = Block(0, 1)
        b = Block(0, 1)
        mixer = a + b.output

        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])

        with self.assertRaises(AttributeError):
            Block(0, 1) + Block(0, 1).input

        a = Block(0, 1)
        b = Block(0, 1)
        mixer = a.output + b

        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])

        with self.assertRaises(AttributeError):
            Block(0, 1).input + Block(0, 1)


if __name__ == '__main__':
    unittest.main()
