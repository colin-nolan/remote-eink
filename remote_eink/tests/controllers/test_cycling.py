import unittest
from threading import Semaphore
from time import sleep
from typing import Optional

from remote_eink.controllers.cycling import CyclableDisplayController, AutoCyclingDisplayController
from remote_eink.drivers.base import ListenableDisplayDriver
from remote_eink.images import Image
from remote_eink.storage.image.base import ImageStore
from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.controllers._common import AbstractTest
from remote_eink.tests.drivers._common import DummyBaseDisplayDriver
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE


class TestCyclableDisplayController(AbstractTest.TestDisplayController[CyclableDisplayController]):
    """
    Tests for `CyclableDisplayController`.
    """

    def create_display_controller(
        self, image_store: Optional[ImageStore] = None, *args, **kwargs
    ) -> CyclableDisplayController:
        return CyclableDisplayController(
            DummyBaseDisplayDriver(), image_store if image_store is not None else InMemoryImageStore()
        )

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


class TestAutoCyclingDisplayController(AbstractTest.TestDisplayController[AutoCyclingDisplayController]):
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

    def create_display_controller(
        self, image_store: Optional[ImageStore] = None, **kwargs
    ) -> AutoCyclingDisplayController:
        display_controller = AutoCyclingDisplayController(
            DummyBaseDisplayDriver(),
            image_store if image_store is not None else InMemoryImageStore(),
            cycle_image_after_seconds=0.001,
            **kwargs
        )
        self._display_controllers.append(display_controller)
        return display_controller

    def test_start(self):
        # FIXME: work out why image transformers are still being applied
        display_controller = self.create_display_controller(
            InMemoryImageStore([WHITE_IMAGE, BLACK_IMAGE]), image_transformers=()
        )
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
        display_controller.stop()

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


# TODO: test `SleepyDisplayController`


if __name__ == "__main__":
    unittest.main()
