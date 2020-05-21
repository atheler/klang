import unittest

from klang.block import Block
from klang.execution import determine_execution_order


class TestExecutionOrder(unittest.TestCase):
    def test_no_blocks(self):
        execOrder = determine_execution_order([])

        self.assertEqual(execOrder, [])

    def test_single_block(self):
        block = Block()
        execOrder = determine_execution_order([block])

        self.assertEqual(execOrder, [block])

    def test_three_blocks_with_no_connections(self):
        a = Block(1, 1)
        b = Block(1, 1)
        c = Block(1, 1)

        execOrder = determine_execution_order([a, b, c])

        self.assertEqual(execOrder, [a, b, c])

    def test_two_seperated_networks(self):
        a = Block(1, 1)
        b = Block(1, 1)
        c = Block(1, 1)
        b.output.connect(c.input)

        execOrder = determine_execution_order([a, b])

        self.assertEqual(execOrder, [a, b, c])


if __name__ == '__main__':
    unittest.main()
