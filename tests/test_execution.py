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

    def test_internal_composite_blocks(self):
        pass


if __name__ == '__main__':
    unittest.main()
