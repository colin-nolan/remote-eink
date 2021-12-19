import unittest
from abc import abstractmethod
from typing import Generic, TypeVar
from unittest.mock import MagicMock

from remote_eink.drivers.base import DisplayDriver, BaseDisplayDriver, ListenableDisplayDriver
from remote_eink.tests.drivers._common import DummyBaseDisplayDriver
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE

DisplayDriverType = TypeVar("DisplayDriverType", bound=DisplayDriver)
BaseDisplayDriverType = TypeVar("BaseDisplayDriverType", bound=BaseDisplayDriver)


class AbstractTest:
    class TestDisplayDriver(Generic[DisplayDriverType], unittest.TestCase):
        """
        Tests for `DisplayDriver`.
        """

        @abstractmethod
        def create_display_driver(self) -> DisplayDriverType:
            """
            TODO
            :return:
            """

        def setUp(self):
            super().setUp()
            self.display_driver: DisplayDriverType = self.create_display_driver()

        def test_sleep(self):
            self.assertFalse(self.display_driver.sleeping)
            self.display_driver.sleep()
            self.assertTrue(self.display_driver.sleeping)
            self.display_driver.sleep()
            self.assertTrue(self.display_driver.sleeping)

        def test_wake(self):
            self.assertFalse(self.display_driver.sleeping)
            self.display_driver.sleep()
            assert self.display_driver.sleeping
            self.display_driver.wake()
            self.assertFalse(self.display_driver.sleeping)
            self.display_driver.wake()
            self.assertFalse(self.display_driver.sleeping)

        def test_display(self):
            self.display_driver.display(WHITE_IMAGE)
            self.assertEqual(WHITE_IMAGE, self.display_driver.image)
            self.display_driver.display(BLACK_IMAGE)
            self.assertEqual(BLACK_IMAGE, self.display_driver.image)

        def test_display_when_sleeping(self):
            self.display_driver.sleep()
            assert self.display_driver.sleeping
            self.display_driver.display(WHITE_IMAGE)
            self.assertFalse(self.display_driver.sleeping)

        def test_clear(self):
            self.display_driver.display(WHITE_IMAGE)
            assert self.display_driver.image == WHITE_IMAGE
            self.display_driver.clear()
            self.assertIsNone(self.display_driver.image)


class TestBaseDisplayDriver(AbstractTest.TestDisplayDriver[BaseDisplayDriverType], unittest.TestCase):
    """
    Tests for `BaseDisplayDriver`.
    """

    def create_display_driver(self) -> DisplayDriverType:
        return DummyBaseDisplayDriver()

    def test_init_to_sleeping(self):
        display_driver = DummyBaseDisplayDriver(sleeping=True)
        self.assertTrue(display_driver.sleeping)

    def test_init_with_image(self):
        display_driver = DummyBaseDisplayDriver(image=WHITE_IMAGE)
        self.assertEqual(WHITE_IMAGE, display_driver.image)


class TestListenableDisplayDriver(AbstractTest.TestDisplayDriver[ListenableDisplayDriver], unittest.TestCase):
    """
    Tests for `ListenableDisplayDriver`.
    """

    def setUp(self):
        super().setUp()
        self.listener = MagicMock()

    def create_display_driver(self) -> ListenableDisplayDriver:
        return ListenableDisplayDriver(DummyBaseDisplayDriver())

    def test_listener_display(self):
        self.display_driver.event_listeners.add(self.listener, ListenableDisplayDriver.Event.DISPLAY)
        self.display_driver.display(WHITE_IMAGE)
        self.assertEqual(1, self.listener.call_count)
        self.assertEqual((WHITE_IMAGE,), self.listener.call_args.args)

    def test_listener_clear(self):
        self.display_driver.event_listeners.add(self.listener, ListenableDisplayDriver.Event.CLEAR)
        self.display_driver.clear()
        self.assertEqual(1, self.listener.call_count)
        self.assertEqual((), self.listener.call_args.args)

    def test_listener_sleep(self):
        assert not self.display_driver.sleeping
        self.display_driver.event_listeners.add(self.listener, ListenableDisplayDriver.Event.SLEEP)
        self.display_driver.sleep()
        self.display_driver.sleep()
        self.assertEqual(1, self.listener.call_count)
        self.assertEqual((), self.listener.call_args.args)

    def test_listener_wake(self):
        self.display_driver.sleep()
        self.display_driver.event_listeners.add(self.listener, ListenableDisplayDriver.Event.WAKE)
        self.display_driver.wake()
        self.display_driver.wake()
        self.assertEqual(1, self.listener.call_count)
        self.assertEqual((), self.listener.call_args.args)
