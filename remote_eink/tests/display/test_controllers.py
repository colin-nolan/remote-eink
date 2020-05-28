import unittest
from abc import ABCMeta, abstractmethod
from functools import partial
from threading import Semaphore
from time import sleep
from typing import TypeVar, Generic, Optional
from unittest.mock import MagicMock

from remote_eink.display.controllers import CyclableDisplayController, AutoCyclingDisplayController, DisplayController
from remote_eink.display.drivers import DummyDisplayDriver, ListenableDisplayDriver
from remote_eink.models import Image
from remote_eink.storage.images import InMemoryImageStore, ImageStore
from remote_eink.tests._common import DummyImageTransformer
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE

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

        self.display_controller.driver.event_listeners.add_listener(
            on_image_display, ListenableDisplayDriver.Event.DISPLAY)
        self.display_controller.image_store.add(WHITE_IMAGE)
        self.display_controller.display(WHITE_IMAGE.identifier)
        self.assertTrue(display_semaphore.acquire(timeout=10))
        self.assertEqual(WHITE_IMAGE, self.display_controller.current_image)
        self.assertEqual(WHITE_IMAGE, display_image)

    def test_display_image_already_displayed(self):
        display_listener = MagicMock()
        self.display_controller.image_store.add(WHITE_IMAGE)
        self.display_controller.display(WHITE_IMAGE.identifier)
        self.display_controller.driver.event_listeners.add_listener(
            display_listener, ListenableDisplayDriver.Event.DISPLAY)
        self.display_controller.display(WHITE_IMAGE.identifier)
        self.assertFalse(display_listener.called)

    def test_display_applies_transforms(self):
        display_semaphore = Semaphore(0)
        displayed_image = None

        def on_display(image: Image):
            nonlocal displayed_image, display_semaphore
            displayed_image = image
            display_semaphore.release()

        transformer = DummyImageTransformer(lambda _: BLACK_IMAGE)
        self.display_controller.driver.event_listeners.add_listener(on_display, ListenableDisplayDriver.Event.DISPLAY)
        self.display_controller.image_transformers.add(transformer)

        self.display_controller.image_store.add(WHITE_IMAGE)
        self.display_controller.display(WHITE_IMAGE.identifier)
        self.assertTrue(display_semaphore.acquire(timeout=15))

        self.assertEqual(WHITE_IMAGE, self.display_controller.current_image)
        self.assertEqual(BLACK_IMAGE, displayed_image)

    def test_image_transforms_when_none_defined(self):
        self.assertEqual(WHITE_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

    def test_image_transform(self):
        transformer = DummyImageTransformer(lambda _: BLACK_IMAGE)
        self.display_controller.image_transformers.add(transformer)
        self.assertEqual(BLACK_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

    def test_image_transform_when_not_active(self):
        transformer = DummyImageTransformer(lambda _: BLACK_IMAGE, active=False)
        self.display_controller.image_transformers.add(transformer)
        self.assertEqual(WHITE_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

    def test_image_transform_multi_transformers(self):
        call_order = []

        def transform(transformer_id: int, image: Image) -> Image:
            call_order.append(transformer_id)
            return image

        transformers = []
        for i in range(16):
            transformer = DummyImageTransformer(partial(transform, i), active=i % 4 != 0)
            transformers.append(transformer)
            self.display_controller.image_transformers.add(transformer)
        self.display_controller.apply_image_transforms(WHITE_IMAGE)
        self.assertEqual([i for i, transformer in enumerate(transformers) if transformer.active], call_order)


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
        image_store = InMemoryImageStore([WHITE_IMAGE])
        display_controller = self.create_display_controller(image_store)
        self.assertEqual(WHITE_IMAGE, display_controller.display_next_image())
        self.assertEqual(WHITE_IMAGE, display_controller.current_image)
        self.assertEqual(WHITE_IMAGE, display_controller.display_next_image())
        self.assertEqual(WHITE_IMAGE, display_controller.current_image)

    def test_display_next_image_when_multiple_image(self):
        image_store = InMemoryImageStore([WHITE_IMAGE, BLACK_IMAGE])
        display_controller = self.create_display_controller(image_store)
        first_image = display_controller.display_next_image()
        second_image = display_controller.display_next_image()
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), (first_image, second_image))
        self.assertNotEqual(first_image, second_image)

    def test_display_next_image_when_image_removed_and_no_left(self):
        image_store = InMemoryImageStore([WHITE_IMAGE])
        display_controller = self.create_display_controller(image_store)
        self.assertEqual(WHITE_IMAGE, display_controller.display_next_image())
        self.assertEqual(WHITE_IMAGE, display_controller.current_image)
        display_controller.image_store.remove(WHITE_IMAGE.identifier)
        self.assertIsNone(display_controller.current_image)

    def test_display_next_image_when_image_removed_and_some_left(self):
        image_store = InMemoryImageStore([WHITE_IMAGE, BLACK_IMAGE])
        display_controller = self.create_display_controller(image_store)
        first_image = display_controller.display_next_image()
        display_controller.image_store.remove(first_image.identifier)
        self.assertIsNotNone(display_controller.current_image)
        self.assertNotEqual(first_image, display_controller.current_image)

    def test_display_next_image_when_image_added(self):
        image_store = InMemoryImageStore([WHITE_IMAGE])
        display_controller = self.create_display_controller(image_store)
        display_controller.display_next_image()
        display_controller.image_store.add(BLACK_IMAGE)
        display_controller.display_next_image()
        self.assertEqual(BLACK_IMAGE, display_controller.current_image)


class TestAutoCyclingDisplayController(_TestDisplayController[AutoCyclingDisplayController]):
    """
    Test for `AutoCyclingDisplayController`.
    """
    def setUp(self):
        self._display_controllers = []
        super().setUp()

    def tearDown(self):
        for display_controller in self._display_controllers:
            display_controller.stop()
        super().tearDown()

    def create_display_controller(self, image_store: Optional[ImageStore] = None, *args, **kwargs) \
            -> AutoCyclingDisplayController:
        display_controller = AutoCyclingDisplayController(
            DummyDisplayDriver(), image_store if image_store is not None else InMemoryImageStore(),
            cycle_image_after_seconds=0.001)
        self._display_controllers.append(display_controller)
        return display_controller

    def test_start(self):
        display_controller = self.create_display_controller(InMemoryImageStore([WHITE_IMAGE, BLACK_IMAGE]))
        images = list()
        call_semaphore = Semaphore(0)

        def listener(image: Image):
            nonlocal call_semaphore
            nonlocal images
            call_semaphore.release()
            images.append(image)

        display_controller.driver.event_listeners.add_listener(listener, ListenableDisplayDriver.Event.DISPLAY)
        display_controller.start()
        for _ in range(10):
            self.assertTrue(call_semaphore.acquire(timeout=10))

        self.assertIn(WHITE_IMAGE, images)
        self.assertIn(BLACK_IMAGE, images)

    def test_stop(self):
        display_controller = self.create_display_controller(InMemoryImageStore([WHITE_IMAGE, BLACK_IMAGE]))
        changes = 0

        def listener(image: Image):
            nonlocal changes
            changes += 1

        display_controller.driver.event_listeners.add_listener(listener, ListenableDisplayDriver.Event.DISPLAY)
        display_controller.start()
        display_controller.stop()
        end_changes = changes
        sleep(display_controller.cycle_image_after_seconds * 25)
        self.assertEqual(end_changes, changes)


del _TestDisplayController

if __name__ == "__main__":
    unittest.main()
