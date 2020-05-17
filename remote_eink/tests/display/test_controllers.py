import unittest

from remote_eink.display.controllers import CyclingDisplayController
from remote_eink.display.drivers import DummyDisplayDriver
from remote_eink.storage.images import InMemoryImageStore
from remote_eink.tests.storage._common import EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2


class TestCyclingDisplayController(unittest.TestCase):
    """
    Test for `CyclingDisplayController`.
    """
    def setUp(self):
        self.driver = DummyDisplayDriver()

    def test_display_next_image_when_no_images(self):
        display_controller = CyclingDisplayController(self.driver, InMemoryImageStore([]), cycle_images=False)
        self.assertIsNone(display_controller.display_next_image())
        self.assertIsNone(display_controller.current_image)
        self.assertIsNone(display_controller.display_next_image())
        self.assertIsNone(display_controller.current_image)

    def test_display_next_image_when_single_image(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = CyclingDisplayController(self.driver, image_store, cycle_images=False)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)

    def test_display_next_image_when_multiple_image(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        display_controller = CyclingDisplayController(self.driver, image_store, cycle_images=False)
        first_image = display_controller.display_next_image()
        second_image = display_controller.display_next_image()
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), (first_image, second_image))
        self.assertNotEqual(first_image, second_image)

    def test_display_next_image_when_image_removed_and_no_left(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = CyclingDisplayController(self.driver, image_store, cycle_images=False)
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.display_next_image())
        self.assertEqual(EXAMPLE_IMAGE_1, display_controller.current_image)
        display_controller.image_store.remove(EXAMPLE_IMAGE_1.identifier)
        self.assertIsNone(display_controller.current_image)

    def test_display_next_image_when_image_removed_and_some_left(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        display_controller = CyclingDisplayController(self.driver, image_store, cycle_images=False)
        first_image = display_controller.display_next_image()
        display_controller.image_store.remove(first_image.identifier)
        self.assertIsNotNone(display_controller.current_image)
        self.assertNotEqual(first_image, display_controller.current_image)

    def test_display_next_image_when_image_added(self):
        image_store = InMemoryImageStore([EXAMPLE_IMAGE_1])
        display_controller = CyclingDisplayController(self.driver, image_store, cycle_images=False)
        display_controller.display_next_image()
        display_controller.image_store.add(EXAMPLE_IMAGE_2)
        display_controller.display_next_image()
        self.assertEqual(EXAMPLE_IMAGE_2, display_controller.current_image)


if __name__ == "__main__":
    unittest.main()
