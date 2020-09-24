"""Test various connection types. Result of multiple development iterations
therefore some duplicated tests.
"""
import unittest

from klang.connections import (
    IncompatibleConnection,
    Input,
    InputAlreadyConnected,
    InputBase,
    MessageInput,
    MessageOutput,
    MessageRelay,
    Output,
    OutputBase,
    Relay,
    RelayBase,
    are_connected,
    is_connected,
    is_valid_connection,
)


class TestConnections(unittest.TestCase):

    """Helper functions for connection testing."""

    def assert_connected(self, *connectables):
        """Assert that each pair of connectables is connected to each other."""
        for con in connectables:
            self.assertTrue(con.connected)

        self.assertTrue(are_connected(*connectables))

    def assert_not_connected(self, *connectables):
        """Assert that each pair of connectables is NOT connected to each
        other.
        """
        for con in connectables:
            self.assertFalse(con.connected)

        self.assertFalse(are_connected(*connectables))


class TestConnectables(TestConnections):
    def test_connect_and_disconnect(self):
        src = OutputBase()
        dst = InputBase()

        self.assert_not_connected(src, dst)

        src.connect(dst)

        self.assert_connected(src, dst)

        src.disconnect(dst)

        self.assert_not_connected(src, dst)

        # And reverse direction
        dst.connect(src)

        self.assert_connected(src, dst)

    def test_wrong_coupling(self):
        with self.assertRaises(IncompatibleConnection):
            InputBase().connect(InputBase())

        with self.assertRaises(IncompatibleConnection):
            OutputBase().connect(OutputBase())

    def test_one_to_many_connections(self):
        src = OutputBase()
        destinatons = [
            InputBase(),
            InputBase(),
            InputBase(),
        ]

        for dst in destinatons:
            src.connect(dst)

        for dst in destinatons:
            self.assert_connected(src, dst)

    def test_input_already_connected(self):
        anOutput = OutputBase()
        input_ = InputBase()
        anOtherOutput = OutputBase()
        anOutput.connect(input_)

        with self.assertRaises(InputAlreadyConnected):
            anOtherOutput.connect(input_)


class TestValueConnections(TestConnections):
    def test_default_value(self):
        src = Output(value=42)
        dst = Input(value=0)

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, 0)

        src.connect(dst)

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, 42)

    def test_value_flow(self):
        nothing = 'not yet set'
        src = Output(value=nothing)
        dst = Input(value=nothing)
        src.connect(dst)

        self.assertEqual(src.value, nothing)
        self.assertEqual(dst.value, nothing)
        self.assertEqual(src.get_value(), nothing)
        self.assertEqual(dst.get_value(), nothing)

        src.set_value(42)

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, 42)
        self.assertEqual(src.get_value(), 42)
        self.assertEqual(dst.get_value(), 42)

        src.value = 43

        self.assertEqual(src.value, 43)
        self.assertEqual(dst.value, 43)
        self.assertEqual(src.get_value(), 43)
        self.assertEqual(dst.get_value(), 43)

    def test_only_input_to_output_connections(self):
        with self.assertRaises(IncompatibleConnection):
            Output().connect(Output())

        with self.assertRaises(IncompatibleConnection):
            Input().connect(Input())


class TestMessageConnections(unittest.TestCase):
    def test_message_flow_from_one_to_many(self):
        src = MessageOutput()
        destinatons = [
            MessageInput(),
            MessageInput(),
            MessageInput(),
        ]

        for dst in destinatons:
            src.connect(dst)

        messages = ['This', 'is', 'it']
        for msg in messages:
            src.send(msg)

        for dst in destinatons:
            self.assertEqual(list(dst.queue), messages)

    def test_receive(self):
        input_ = MessageInput()
        messages = list(range(10))
        for msg in messages:
            input_.push(msg)

        self.assertEqual(len(input_.queue), 10)
        self.assertEqual(list(input_.receive()), messages)
        self.assertEqual(len(input_.queue), 0)

    def test_receive_latest(self):
        input_ = MessageInput()

        self.assertIs(input_.receive_latest(), None)

        messages = list(range(10))
        for msg in messages:
            input_.push(msg)

        self.assertEqual(len(input_.queue), 10)
        self.assertEqual(input_.receive_latest(), 9)
        self.assertEqual(len(input_.queue), 0)


class TestRelay(TestConnections):
    def test_is_valid_connection(self):
        self.assertTrue(is_valid_connection(OutputBase(), InputBase()))
        self.assertTrue(is_valid_connection(OutputBase(), RelayBase()))
        self.assertTrue(is_valid_connection(RelayBase(), RelayBase()))
        self.assertTrue(is_valid_connection(RelayBase(), InputBase()))

        # Onto itself
        self.assertFalse(is_valid_connection(InputBase(), InputBase()))
        self.assertTrue(is_valid_connection(RelayBase(), RelayBase()))
        self.assertFalse(is_valid_connection(OutputBase(), OutputBase()))

        # Value
        self.assertFalse(is_valid_connection(MessageOutput(), InputBase()))
        self.assertFalse(is_valid_connection(MessageOutput(), RelayBase()))
        self.assertFalse(is_valid_connection(OutputBase(), MessageInput()))
        self.assertFalse(is_valid_connection(RelayBase(), MessageInput()))

    def test_relay_base_only_one_input_connection(self):
        relay = RelayBase()
        OutputBase().connect(relay)

        with self.assertRaises(InputAlreadyConnected):
            OutputBase().connect(relay)

    @staticmethod
    def fresh_connections():
        """Generate a fresh connection triple"""
        return OutputBase(), RelayBase(), InputBase()

    def test_connect_and_disconnect_with_relay(self):

        # Note: assertFalse(is_connected(...)) instead of
        # assert_not_connected(...) since a relay can be "connected" to e.g. an
        # output whilst not being connected to another input.

        # src -> relay -> dst
        src, relay, dst = self.fresh_connections()
        src.connect(relay)
        relay.connect(dst)

        self.assert_connected(src, relay, dst)

        # src -> relay, relay -> dst
        src, relay, dst = self.fresh_connections()
        src.connect(relay)

        self.assertTrue(is_connected(src, relay))
        self.assertFalse(is_connected(relay, dst))

        relay.connect(dst)

        self.assert_connected(src, relay, dst)

        # relay -> dst, src -> relay
        src, relay, dst = self.fresh_connections()
        relay.connect(dst)

        self.assertFalse(is_connected(src, relay))
        self.assertTrue(is_connected(relay, dst))

        src.connect(relay)

        self.assert_connected(src, relay, dst)

        # relay <- src, dst <- relay
        src, relay, dst = self.fresh_connections()
        relay.connect(src)

        self.assertTrue(is_connected(src, relay))
        self.assertFalse(is_connected(relay, dst))

        dst.connect(relay)

        self.assert_connected(src, relay, dst)

        # dst <- relay, relay <- src,
        src, relay, dst = self.fresh_connections()
        dst.connect(relay)

        self.assertFalse(is_connected(src, relay))
        self.assertTrue(is_connected(relay, dst))

        relay.connect(src)

        self.assert_connected(src, relay, dst)

        # dst <- relay <- src
        src, relay, dst = self.fresh_connections()
        dst.connect(relay)
        relay.connect(src)

        self.assert_connected(src, relay, dst)

    def test_value_flow_with_relay(self):
        src = Output(value=42)
        dst = Input(value=-1)
        relay = Relay()

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, -1)

        src.connect(relay)
        relay.connect(dst)

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, 42)

        src.set_value(666)

        self.assertEqual(src.value, 666)
        self.assertEqual(dst.value, 666)

    def test_message_flow_with_relay(self):
        src = MessageOutput()
        dst = MessageInput()
        relay = MessageRelay()
        src.connect(relay)
        relay.connect(dst)
        src.send('Hello World')

        self.assertEqual(dst.receive_latest(), 'Hello World')

    def test_message_flow_from_one_to_many_with_relay(self):
        src = MessageOutput()
        relay = MessageRelay()
        destinatons = [
            MessageInput(),
            MessageInput(),
            MessageInput(),
        ]

        src.connect(relay)

        for dst in destinatons:
            relay.connect(dst)

        msg = 'this is it'
        src.send(msg)

        for dst in destinatons:
            self.assertEqual(dst.receive_latest(), msg)


if __name__ == '__main__':
    unittest.main()
