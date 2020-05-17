import unittest
from unittest.mock import MagicMock, call

from remote_eink.events import EventListenerController


class TestEventListenerController(unittest.TestCase):
    """
    Tests `EventListenerController`.
    """
    def setUp(self):
        self.event_listeners = EventListenerController[int]()

    def test_add_listener(self):
        listener = MagicMock()
        self.event_listeners.add_listener(listener, 0)
        self.assertEqual({listener}, self.event_listeners.get_listeners(0))
        self.assertEqual({0}, self.event_listeners.get_events())

    def test_add_listener_to_different_events(self):
        listener = MagicMock()
        self.event_listeners.add_listener(listener, 0)
        self.event_listeners.add_listener(listener, 1)
        self.assertEqual({listener}, self.event_listeners.get_listeners(0))
        self.assertEqual({listener}, self.event_listeners.get_listeners(1))

    def test_add_listener_twice(self):
        listener = MagicMock()
        self.event_listeners.add_listener(listener, 0)
        self.assertRaises(ValueError, self.event_listeners.add_listener, listener, 0)

    def test_remove_listener(self):
        listener = MagicMock()
        self.event_listeners.add_listener(listener, 0)
        self.event_listeners.remove_listener(listener, 0)
        self.assertEqual(set(), self.event_listeners.get_listeners(0))

    def test_remove_listener_not_exist(self):
        self.event_listeners.remove_listener(MagicMock(), 0)

    def test_call_listeners(self):
        listeners = [MagicMock() for _ in range(10)]
        other_listeners = [MagicMock() for _ in range(10)]
        for listener in listeners:
            self.event_listeners.add_listener(listener, 0)
        for i, listener in enumerate(other_listeners):
            self.event_listeners.add_listener(listener, i + 10)

        self.event_listeners.call_listeners(0, [42], dict(a=84))

        for listener in listeners:
            self.assertEqual(1, listener.call_count)
            self.assertEqual(call(42, a=84), listener.call_args)
        for listener in other_listeners:
            self.assertFalse(listener.called)

    def test_listener_return_values(self):
        listener_1 = lambda: 42
        listener_2 = lambda: 84
        self.event_listeners.add_listener(listener_1, 0)
        self.event_listeners.add_listener(listener_2, 0)
        returns = self.event_listeners.call_listeners(0)
        self.assertEqual(listener_1(), returns[listener_1]())
        self.assertEqual(listener_2(), returns[listener_2]())

    def test_listener_return_exceptions(self):
        def listener_1():
            raise ValueError()

        def listener_2():
            raise RuntimeError()

        self.event_listeners.add_listener(listener_1, 0)
        self.event_listeners.add_listener(listener_2, 0)
        returns = self.event_listeners.call_listeners(0)
        self.assertRaises(ValueError, returns[listener_1])
        self.assertRaises(RuntimeError, returns[listener_2])


if __name__ == "__main__":
    unittest.main()
