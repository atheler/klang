"""Test helper functions of operation overloading."""
import unittest

from klang.block import Block
from klang.audio.mixer import Mixer
from klang.operations import NotPipeable, NotMixable, pipe, mix


class TestOperations(unittest.TestCase):

    """Test the base operations pipe() and mix()."""

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

    def test_pipe(self):
        a = Block(nOutputs=1)
        b = Block(nInputs=1)

        self.assertIs(pipe(a, b), b)
        self.assert_is_connected(a, b)

    def test_mix(self):
        a = Block(nOutputs=1)
        b = Block(nOutputs=1)
        mixer = mix(a, b)

        self.assertTrue(isinstance(mixer, Mixer))
        self.assert_is_connected(a, mixer.inputs[0])
        self.assert_is_connected(b, mixer.inputs[1])

        c = Block(nOutputs=1)
        mixer2 = mix(mixer, c)

        self.assertIs(mixer, mixer2)
        self.assert_is_connected(c, mixer.inputs[2])

    def test_invalid_pipeings(self):
        with self.assertRaises(NotPipeable):
            pipe(Block(), Block())

        with self.assertRaises(NotPipeable):
            pipe(Block(nInputs=1), Block(nInputs=1))

        with self.assertRaises(NotPipeable):
            pipe(Block(nInputs=1), Block(nOutputs=1))

        with self.assertRaises(NotPipeable):
            pipe(Block(nOutputs=1), Block(nOutputs=1))

    def test_invalid_mixes(self):
        with self.assertRaises(NotMixable):
            mix(Block(), Block())

        with self.assertRaises(NotMixable):
            mix(Block(nOutputs=1), Block(nInputs=1))

        with self.assertRaises(NotMixable):
            mix(Block(nInputs=1), Block(nInputs=1))


if __name__ == '__main__':
    unittest.main()
