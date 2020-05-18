import unittest
from abc import ABCMeta, abstractmethod
from threading import Semaphore
from time import sleep
from typing import TypeVar, Generic, Optional
from unittest.mock import MagicMock

from remote_eink.display.controllers import CyclableDisplayController, AutoCyclingDisplayController, DisplayController
from remote_eink.display.drivers import DummyDisplayDriver, DisplayDriverEvent
from remote_eink.models import Image
from remote_eink.storage.images import InMemoryImageStore, ImageStore
from remote_eink.tests.storage._common import EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2

_DisplayControllerType = TypeVar("_DisplayControllerType", bound=DisplayController)


class _TestDisplayController(unittest.TestCase, Generic[_DisplayControllerType], metaclass=ABCMeta):
    """
    Tests for `DisplayController` implementations.
    """
    @abstractmethod
    def create_display_controller(self, image_store: Optional[ImageStore] = None, *args, **kwargs) \
            -> _DisplayControllerType:
        """
        TODO
        :param image_store:
        :param args:
        :param kwargs:
        :return:
        """

    def setUp(self):
        self.display_controller: _DisplayControllerType = self.create_display_controller()

    def test_display_image(self):
        display_semaphore = Semaphore(0)
        display_image = None

        def on_image_display(image):
            nonlocal display_image
            nonlocal display_semaphore
            display_image = image
            display_semaphore.release()

        self.display_controller.driver.event_listeners.add_listener(on_image_display, DisplayDriverEvent.DISPLAY)
        self.display_controller.image_store.add(EXAMPLE_IMAGE_1)
        self.display_controller.display(EXAMPLE_IMAGE_1.identifier)
        display_semaphore.acquire(timeout=10)
        self.assertEqual(EXAMPLE_IMAGE_1, self.display_controller.current_image)
        self.assertEqual(EXAMPLE_IMAGE_1, display_image)

    def test_display_image_already_displayed(self):
        display_listener = MagicMock()
        self.display_controller.image_store.add(EXAMPLE_IMAGE_1)
        self.display_controller.display(EXAMPLE_IMAGE_1.identifier)
        self.display_controller.driver.event_listeners.add_listener(display_listener, DisplayDriverEvent.DISPLAY)
        self.display_controller.display(EXAMPLE_IMAGE_1.identifier)
        self.assertFalse(display_listener.called)


class TestCyclableDisplayController(_TestDisplayController[CyclableDisplayController]):
    """
    Test for `CyclableDisplayController`.
    """
    def create_display_controller(self, image_store: Optional[ImageStore] = None, *args, **kwargs) \
            -> CyclableDisplayController:
        return CyclableDisplayController(DummyDisplayDriver(),
                                         image_store if image_store is not None else InMemoryImageStore())

    def test_display_next_image_when_no_images(self):
        self.assertIsNone(self.display_controller.display_next_image())
        self.assertIsNone(self.display_controller.current_image)
        self.assertIsNone(self.display_controller.display_next_image())
        self.assertIsNone(self.display_controller.current_image)

    def test_display_next_image_when_single_image(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = self.create_display_controller(image_store)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)

    def test_display_next_image_when_multiple_image(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        display_controller = self.create_display_controller(image_store)
        first_image = display_controller.display_next_image()
        second_image = display_controller.display_next_image()
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), (first_image, second_image))
        self.assertNotEqual(first_image, second_image)

    def test_display_next_image_when_image_removed_and_no_left(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = self.create_display_controller(image_store)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)
        display_controller.image_store.remove(EXAMPLE_IMAGE_1.identifier)
        self.assertIsNone(display_controller.current_image)

    def test_display_next_image_when_image_removed_and_some_left(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        display_controller = self.create_display_controller(image_store)
        first_image = display_controller.display_next_image()
        display_controller.image_store.remove(first_image.identifier)
        self.assertIsNotNone(display_controller.current_image)
        self.assertNotEqual(first_image, display_controller.current_image)

    def test_display_next_image_when_image_added(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = self.create_display_controller(image_store)
        display_controller.display_next_image()
        display_controller.image_store.add(EXAMPLE_IMAGE_2)
        display_controller.display_next_image()
        self.assertEqual(EXAMPLE_IMAGE_2, display_controller.current_image)


class TestAutoCyclingDisplayController(_TestDisplayController[AutoCyclingDisplayController]):
    """
    Test for `AutoCyclingDisplayController`.
    """
    def create_display_controller(self, image_store: Optional[ImageStore] = None, *args, **kwargs) \
            -> AutoCyclingDisplayController:
        return AutoCyclingDisplayController(
            DummyDisplayDriver(), image_store if image_store is not None else InMemoryImageStore(),
            cycle_image_after_seconds=0.001)

    def test_start(self):
        display_controller = self.create_display_controller(InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2]))
        images = list()
        call_semaphore = Semaphore(0)

        def listener(image: Image):
            nonlocal call_semaphore
            nonlocal images
            call_semaphore.release()
            images.append(image)

        display_controller.driver.event_listeners.add_listener(listener, DisplayDriverEvent.DISPLAY)
        display_controller.start()
        for _ in range(10):
            call_semaphore.acquire(timeout=10)

        self.assertIn(EXAMPLE_IMAGE_1, images)
        self.assertIn(EXAMPLE_IMAGE_2, images)

    def test_stop(self):
        display_controller = self.create_display_controller(InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2]))
        changes = 0

        def listener(image: Image):
            nonlocal changes
            changes += 1

        display_controller.driver.event_listeners.add_listener(listener, DisplayDriverEvent.DISPLAY)
        display_controller.start()
        display_controller.stop()
        end_changes = changes
        sleep(display_controller.cycle_image_after_seconds * 25)
        self.assertEqual(end_changes, changes)


del _TestDisplayController

if __name__ == "__main__":
    unittest.main()
