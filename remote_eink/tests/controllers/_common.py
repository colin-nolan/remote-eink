import unittest
from abc import ABCMeta, abstractmethod
from functools import partial
from threading import Semaphore
from typing import Generic, Optional, TypeVar
from unittest.mock import MagicMock

from remote_eink.controllers.base import DisplayController
from remote_eink.drivers.base import ListenableDisplayDriver
from remote_eink.images import Image
from remote_eink.storage.image.base import ImageStore
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE
from remote_eink.transformers.simple import SimpleImageTransformer

DisplayControllerType = TypeVar("DisplayControllerType", bound=DisplayController)


class AbstractTest:
    """
    https://stackoverflow.com/questions/4566910/abstract-test-case-using-python-unittest
    """

    class TestDisplayController(unittest.TestCase, Generic[DisplayControllerType], metaclass=ABCMeta):
        """
        Tests for `DisplayController` implementations.
        """

        @abstractmethod
        def create_display_controller(
            self, image_store: Optional[ImageStore] = None, *args, **kwargs
        ) -> DisplayControllerType:
            """
            Creates display controller to test.
            :param image_store: image store that the display controller is to have
            :param args: positional arguments to pass to the display controller
            :param kwargs: keyword arguments to pass to the display controller
            :return: created display controller
            """

        def setUp(self):
            super().setUp()
            self.display_controller: DisplayControllerType = self.create_display_controller()

        def test_display_image(self):
            display_semaphore = Semaphore(0)
            display_image = None

            def on_image_display(image):
                nonlocal display_image
                nonlocal display_semaphore
                display_image = image
                display_semaphore.release()

            self.display_controller.driver.event_listeners.add_listener(
                on_image_display, ListenableDisplayDriver.Event.DISPLAY
            )
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
                display_listener, ListenableDisplayDriver.Event.DISPLAY
            )
            self.display_controller.display(WHITE_IMAGE.identifier)
            self.assertFalse(display_listener.called)

        def test_display_applies_transforms(self):
            display_semaphore = Semaphore(0)
            displayed_image = None

            def on_display(image: Image):
                nonlocal displayed_image, display_semaphore
                displayed_image = image
                display_semaphore.release()

            transformer = SimpleImageTransformer(lambda _: BLACK_IMAGE)
            self.display_controller.driver.event_listeners.add_listener(
                on_display, ListenableDisplayDriver.Event.DISPLAY
            )
            self.display_controller.image_transformers.add(transformer)

            self.display_controller.image_store.add(WHITE_IMAGE)
            self.display_controller.display(WHITE_IMAGE.identifier)
            self.assertTrue(display_semaphore.acquire(timeout=15))

            self.assertEqual(WHITE_IMAGE, self.display_controller.current_image)
            self.assertEqual(BLACK_IMAGE, displayed_image)

        def test_image_transforms_when_none_defined(self):
            self.assertEqual(WHITE_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

        def test_image_transform(self):
            transformer = SimpleImageTransformer(lambda _: BLACK_IMAGE)
            self.display_controller.image_transformers.add(transformer)
            self.assertEqual(BLACK_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

        def test_image_transform_when_not_active(self):
            transformer = SimpleImageTransformer(lambda _: BLACK_IMAGE, active=False)
            self.display_controller.image_transformers.add(transformer)
            self.assertEqual(WHITE_IMAGE, self.display_controller.apply_image_transforms(WHITE_IMAGE))

        def test_image_transform_multi_transformers(self):
            call_order = []

            def transform(transformer_id: int, image: Image) -> Image:
                call_order.append(transformer_id)
                return image

            transformers = []
            for i in range(16):
                transformer = SimpleImageTransformer(partial(transform, i), active=i % 4 != 0)
                transformers.append(transformer)
                self.display_controller.image_transformers.add(transformer)
            self.display_controller.apply_image_transforms(WHITE_IMAGE)
            self.assertEqual([i for i, transformer in enumerate(transformers) if transformer.active], call_order)
