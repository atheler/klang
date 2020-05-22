import unittest

from klang.block import Block
from klang.composite import Composite, temporarily_unpatch
from klang.connections import Relay


class TestTemporarilyUnpatch(unittest.TestCase):
    def test_temporarily_unpatch(self):
        src = Block(0, 1)
        block = Block(1, 1)
        dst0 = Block(1, 0)
        dst1 = Block(1, 0)

        src | block | dst0
        block | dst1

        with temporarily_unpatch(block):
            self.assertFalse(block.input.connected)
            self.assertFalse(block.output.connected)

        self.assertIs(block.input.incomingConnection, src.output)
        self.assertEqual(block.output.outgoingConnections, {dst0.input, dst1.input})


class TestComposite(unittest.TestCase):
    def test_exeuction_order(self):
        comp = Composite()
        comp.inputs = [Relay(owner=comp), Relay(owner=comp)]
        comp.outputs = [Relay(owner=comp), Relay(owner=comp)]
        a = Block(nInputs=1, nOutputs=1)
        b = Block(nInputs=1, nOutputs=1)
        comp.inputs[0] | a | comp.outputs[0]
        comp.inputs[1] | b | comp.outputs[1]
        comp.update_internal_exec_order()

        self.assertEqual(comp.execOrder, [a, b])

    def test_patching(self):
        comp = Composite()
        comp.inputs = [Relay(owner=comp)]
        comp.outputs = [Relay(owner=comp)]


if __name__ == '__main__':
    unittest.main()
