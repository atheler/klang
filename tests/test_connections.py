"""Test various connection types. Result of multiple development iterations
therefore some duplicated tests.
"""
import unittest

from klang.connections import (
    is_valid_connection,
    AlreadyConnectedError,
    IncompatibleError,
    Input,
    InputBase,
    MessageInput,
    MessageOutput,
    MessageRelay,
    Output,
    OutputBase,
    Relay,
    RelayBase,
)


class TestConnectables(unittest.TestCase):
    def test_connection(self):
        a = OutputBase(owner=None)
        b = InputBase(owner=None)
        a.connect(b)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

        self.assertIn(b, a.outgoingConnections)
        self.assertEqual(a, b.incomingConnection)

    def test_disconnect(self):
        a = OutputBase(owner=None)
        b = InputBase(owner=None)
        a.connect(b)

        a.disconnect(b)

        self.assertFalse(a.connected)
        self.assertFalse(b.connected)

    def test_one_to_many_connections(self):
        a = OutputBase(owner=None)
        b = InputBase(owner=None)
        c = InputBase(owner=None)

        a.connect(b)
        a.connect(c)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)
        self.assertTrue(c.connected)

        self.assertIn(b, a.outgoingConnections)
        self.assertIn(c, a.outgoingConnections)
        self.assertIs(a, b.incomingConnection)
        self.assertIs(a, c.incomingConnection)

    def test_already_connected(self):
        a = OutputBase()
        b = InputBase()
        c = OutputBase()
        a.connect(b)

        with self.assertRaises(AlreadyConnectedError):
            c.connect(b)

        b.disconnect(a)
        #c.connect(b)


class TestInputOutput(unittest.TestCase):
    def test_one_to_many(self):
        src = Output(None)
        a = Input(None)
        b = Input(None)

        src.connect(a)
        src.connect(b)

        self.assertTrue(src.connected)
        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

        self.assertIs(src, a.incomingConnection)
        self.assertIs(src, b.incomingConnection)
        self.assertIn(a, src.outgoingConnections)
        self.assertIn(b, src.outgoingConnections)

    def test_only_one_connection_per_input(self):
        a = Output(None)
        b = Output(None)
        dst = Input(None)

        dst.connect(b)

        with self.assertRaises(AlreadyConnectedError):
            dst.connect(b)

    def test_value_transfer(self):
        nothing = 'not yet set'
        src = Output(None, value=nothing)
        dst = Input(None, value=nothing)
        src.connect(dst)

        self.assertEqual(src.value, nothing)
        self.assertEqual(dst.value, nothing)
        self.assertEqual(src.get_value(), nothing)
        self.assertEqual(dst.get_value(), nothing)

        src.value = 42

        self.assertEqual(src.value, 42)
        self.assertEqual(dst.value, 42)
        self.assertEqual(src.get_value(), 42)
        self.assertEqual(dst.get_value(), 42)

    def test_only_input_to_output_connections(self):
        with self.assertRaises(IncompatibleError):
            Output().connect(Output())

        with self.assertRaises(IncompatibleError):
            Input().connect(Input())


class TestMessageInputOutput(unittest.TestCase):
    def test_message_flow(self):
        src = MessageOutput(None)
        dst = MessageInput(None)

        src.connect(dst)
        msg = 'Hello World!'
        src.send(msg)

        self.assertEqual(next(dst.receive()), msg)

    def test_receive(self):
        input = MessageInput()
        messages = list(range(10))
        for msg in messages:
            input.push(msg)

        self.assertEqual(list(input.receive()), messages)
        self.assertEqual(len(input.queue), 0)

    def test_receive_latest(self):
        input = MessageInput()

        self.assertIs(input.receive_latest(), None)

        messages = list(range(10))
        for msg in messages:
            input.push(msg)

        self.assertEqual(input.receive_latest(), 9)
        self.assertEqual(len(input.queue), 0)

    def test_one_to_many(self):
        src = MessageOutput()
        destinations = [MessageInput(), MessageInput(), MessageInput()]
        for dst in destinations:
            src.connect(dst)

        messages = ['This', 'is', 'it']
        for msg in messages:
            src.send(msg)

        for dst in destinations:
            self.assertEqual(list(dst.receive()), messages)


class TestNewConnections(unittest.TestCase):
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

    def test_input_output_base_classes(self):
        a = OutputBase()
        b = InputBase()

        self.assertFalse(a.connected)
        self.assertFalse(b.connected)

        with self.assertRaises(IncompatibleError):
            a.connect(a)

        with self.assertRaises(IncompatibleError):
            b.connect(b)

        a.connect(b)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

        with self.assertRaises(AlreadyConnectedError):
            a.connect(b)

    def test_connecting_both_ways(self):
        a = OutputBase()
        b = InputBase()

        a.connect(b)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

        a.disconnect(b)

        self.assertFalse(a.connected)
        self.assertFalse(b.connected)

        b.connect(a)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

    def test_relay_base_class(self):
        a = OutputBase()
        b = InputBase()
        r = RelayBase()

        a.connect(r)
        r.connect(b)

        self.assertTrue(r.connected)

    def test_relay_base_class_in_reverse_direction(self):
        a = OutputBase()
        b = InputBase()
        r = RelayBase()

        b.connect(r)
        r.connect(a)

        self.assertTrue(r.connected)

    def test_value_connection(self):
        a = Output()
        b = Input()

        self.assertEqual(a.value, 0.)
        self.assertEqual(b.value, 0.)

        a.connect(b)
        a.set_value(666)

        self.assertEqual(a.value, 666)
        self.assertEqual(b.value, 666)

    def test_value_connection_with_relay(self):
        a = Output()
        b = Input()
        r = Relay()

        a.connect(r)
        r.connect(b)

        a.set_value(666)

        self.assertEqual(b.value, 666)

    def test_message_connection(self):
        a = MessageOutput()
        b = MessageInput()
        c = MessageInput()

        a.connect(b)
        a.connect(c)

        a.send('this')
        a.send('is')
        a.send('it')

        self.assertEqual(list(b.receive()), ['this', 'is', 'it'])
        self.assertEqual(c.receive_latest(), 'it')

    def test_message_connection_with_relay(self):
        a = MessageOutput()
        b = MessageInput()
        r = MessageRelay()

        a.connect(r)
        r.connect(b)

        a.send('Hello World')

        self.assertEqual(b.receive_latest(), 'Hello World')

    def test_relay_base_only_one_input_connection(self):
        a = OutputBase()
        r = RelayBase()
        a.connect(r)
        b = OutputBase()

        with self.assertRaises(AlreadyConnectedError):
            b.connect(r)


class TestIncompatibleConnections(unittest.TestCase):
    def test_some_incompatible_connections(self):
        with self.assertRaises(IncompatibleError):
            Output().connect(MessageInput())

        with self.assertRaises(IncompatibleError):
            MessageOutput().connect(Input())


if __name__ == '__main__':
    unittest.main()
