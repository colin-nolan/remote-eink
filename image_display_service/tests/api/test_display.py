import json
import random
from uuid import uuid4

from flask_testing import TestCase
import unittest

from image_display_service.display.controllers import DisplayController
from image_display_service.display.drivers import DummyDisplayDriver, Image
from image_display_service.web_api import create_app


def create_dummy_display_controller(number_of_images: int = 0, has_current_image: bool = False) -> DisplayController:
    """
    TODO
    :param number_of_images:
    :param has_current_image:
    :return:
    """
    if has_current_image and number_of_images == 0:
        raise ValueError("Cannot have current images if no images")
    images = [Image(str(uuid4()), b"") for _ in range(number_of_images)]
    current_image = images[0] if has_current_image > 0 else None
    return DisplayController(driver=DummyDisplayDriver(), identifier=str(uuid4()), current_image=current_image,
                             image_orientation=random.randint(0, 364), images=images,
                             cycle_images=random.choice([True, False]), cycle_randomly=random.choice([True, False]),
                             cycle_image_after_seconds=random.randint(1, 9999))


class DisplayApiTests(TestCase):
    """
    Tests for the `/display` endpoint.
    """
    def create_app(self):
        self.display_controllers = []
        app = create_app(self.display_controllers).app
        app.config["TESTING"] = True
        return app

    def test_search_displays(self):
        display_controllers = [create_dummy_display_controller() for _ in range(10)]
        self.display_controllers.extend(display_controllers)
        result = self.client.get("/display")
        self.assertEqual(200, result.status_code)
        self.assertCountEqual([controller.identifier for controller in display_controllers], json.loads(result.json))

    def test_get_display(self):
        for _ in range(5):
            self.display_controllers.append(create_dummy_display_controller())
        controller = create_dummy_display_controller(10, True)
        self.display_controllers.append(controller)
        for _ in range(5):
            self.display_controllers.append(create_dummy_display_controller())

        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(200, result.status_code)
        content = json.loads(result.json)
        self.assertEqual(controller.identifier, content["id"])
        self.assertEqual(controller.current_image.identifier, content["currentImage"])
        self.assertCountEqual((image.identifier for image in controller.images), content["images"])
        self.assertEqual(controller.image_orientation, content["orientation"])
        self.assertEqual(controller.cycle_images, content["cycleImages"])
        self.assertEqual(controller.cycle_images_randomly, content["cycleRandomly"])
        self.assertEqual(controller.cycle_image_after_seconds, content["cycleAfterSeconds"])

    def test_get_display_not_exist(self):
        result = self.client.get(f"/display/does-not-exist")
        self.assertEqual(404, result.status_code)

    def test_get_display_with_no_images(self):
        controller = create_dummy_display_controller(0)
        self.display_controllers.append(controller)

        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(200, result.status_code)
        content = json.loads(result.json)
        self.assertEqual([], content["images"])
        self.assertIsNone(content["currentImage"])


if __name__ == "__main__":
    unittest.main()
