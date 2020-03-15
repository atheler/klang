import unittest

from klang.connections import (
    AlreadyConnectedError,
    Connectable,
    Input,
    MessageInput,
    MessageOutput,
    NotConnectableError,
    Output,
)


class TestConnectables(unittest.TestCase):
    def test_connection(self):
        a = Connectable(None)
        b = Connectable(None)
        a.connect(b)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)

        self.assertIn(b, a.connections)
        self.assertIn(a, b.connections)

    def test_disconnect(self):
        a = Connectable(None)
        b = Connectable(None)
        a.connect(b)

        a.disconnect(b)

        self.assertFalse(a.connected)
        self.assertFalse(b.connected)

    def test_single_connection(self):
        a = Connectable(None, singleConnection=True)
        b = Connectable(None)
        a.connect(b)

    def test_already_connected_with_single_connection_both_ways(self):
        a = Connectable(None, singleConnection=True)
        b = Connectable(None)
        c = Connectable(None)
        a.connect(b)

        with self.assertRaises(AlreadyConnectedError):
            a.connect(c)

        with self.assertRaises(AlreadyConnectedError):
            c.connect(a)

    def test_one_to_many_connections(self):
        a = Connectable(None)
        b = Connectable(None)
        c = Connectable(None)

        a.connect(b)
        a.connect(c)

        self.assertTrue(a.connected)
        self.assertTrue(b.connected)
        self.assertTrue(c.connected)

        self.assertIn(b, a.connections)
        self.assertIn(c, a.connections)
        self.assertIn(a, b.connections)
        self.assertIn(a, c.connections)

    """
    def test_already(self):
        a = Connectable(None)
        b = Connectable(None)
        c = Connectable(None)

        a.connect(b)

        with self.assertRaises(AlreadyConnectedError):
            a.connect(b)
    """

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
        self.assertIn(src, a.connections)
        self.assertIn(src, b.connections)
        self.assertIn(a, src.connections)
        self.assertIn(b, src.connections)

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
        a = Output(None)
        b = Output(None)
        c = Input(None)
        d = Input(None)

        with self.assertRaises(NotConnectableError):
            a.connect(b)

        with self.assertRaises(NotConnectableError):
            c.connect(d)


class TestMessageInputOutput(unittest.TestCase):
    def test_message_flow(self):
        src = MessageOutput(None)
        dst = MessageInput(None)

        src.connect(dst)
        msg = 'Hello World!'
        src.send(msg)

        self.assertEqual(next(dst.receive()), msg)


if __name__ == '__main__':
    unittest.main()
