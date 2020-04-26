import unittest

from klang.block import Block
from klang.audio.mixer import Mixer


class TestBlock(unittest.TestCase):
    def test_operator_or(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        d = a | b | c

        self.assertIs(d, c)

    def test_operator_and(self):
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        c = Block(nInputs=1, nOutputs=1)
        d = a & b & c

        self.assertIs(type(d), Mixer)


if __name__ == '__main__':
    unittest.main()
