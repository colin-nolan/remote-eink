import json
import random
from abc import ABCMeta
from unittest import skip
from uuid import uuid4

from flask_testing import TestCase
import unittest

from image_display_service.display.controllers import DisplayController
from image_display_service.display.drivers import DummyDisplayDriver
from image_display_service.image import Image
from image_display_service.storage import InMemoryImageStore
from image_display_service.web_api import create_app


def create_dummy_display_controller(*, number_of_images: int = 0, has_current_image: bool = False) -> DisplayController:
    """
    TODO
    :param number_of_images:
    :param has_current_image:
    :return:
    """
    if has_current_image and number_of_images == 0:
        raise ValueError("Cannot have current images if no images")
    image_store = InMemoryImageStore(Image(str(uuid4()), lambda: f"data-{i}".encode()) for i in range(number_of_images))
    current_image = image_store.list()[0] if has_current_image > 0 else None
    return DisplayController(driver=DummyDisplayDriver(), identifier=str(uuid4()), current_image=current_image,
                             image_orientation=random.randint(0, 364), image_store=image_store,
                             cycle_images=random.choice([True, False]), cycle_randomly=random.choice([True, False]),
                             cycle_image_after_seconds=random.randint(1, 9999))


class TestBase(TestCase, metaclass=ABCMeta):
    """
    TODO
    """
    def create_app(self):
        self.display_controllers = []
        app = create_app(self.display_controllers).app
        app.config["TESTING"] = True
        return app

    def create_dummy_display_controller(self, **kwargs) -> DisplayController:
        controller = create_dummy_display_controller(**kwargs)
        self.display_controllers.append(controller)
        return controller


class TestDisplayApi(TestBase):
    """
    Tests for the `/display` endpoint.
    """
    def test_list_displays(self):
        display_controllers = [self.create_dummy_display_controller() for _ in range(10)]
        result = self.client.get("/display")
        self.assertEqual(200, result.status_code)
        self.assertCountEqual([controller.identifier for controller in display_controllers], json.loads(result.json))

    def test_get_display(self):
        for _ in range(5):
            self.create_dummy_display_controller()
        controller = self.create_dummy_display_controller(number_of_images=10, has_current_image=True)
        for _ in range(5):
            self.create_dummy_display_controller()

        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(200, result.status_code)
        content = json.loads(result.json)
        self.assertEqual(controller.identifier, content["id"])
        self.assertEqual(controller.current_image.identifier, content["currentImage"]["id"])
        self.assertCountEqual((image.identifier for image in controller.image_store.list()),
                              (image["id"] for image in content["images"]))
        self.assertEqual(controller.image_orientation, content["orientation"])
        self.assertEqual(controller.cycle_images, content["cycleImages"])
        self.assertEqual(controller.cycle_images_randomly, content["cycleRandomly"])
        self.assertEqual(controller.cycle_image_after_seconds, content["cycleAfterSeconds"])

    def test_get_display_not_exist(self):
        result = self.client.get(f"/display/does-not-exist")
        self.assertEqual(404, result.status_code)

    def test_get_display_with_no_images(self):
        controller = self.create_dummy_display_controller(number_of_images=0)
        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(200, result.status_code)
        content = json.loads(result.json)
        self.assertEqual([], content["images"])
        self.assertIsNone(content["currentImage"])


class TestDisplayImage(TestBase):
    """
    Tests for the `/display/{displayId}/image` endpoint.
    """
    def test_list_display_images(self):
        for number_of_images in range(5):
            with self.subTest(number_of_images=number_of_images):
                controller = self.create_dummy_display_controller(number_of_images=number_of_images)
                result = self.client.get(f"/display/{controller.identifier}/image")
                self.assertEqual(200, result.status_code)
                self.assertCountEqual(({"id": image.identifier} for image in controller.image_store.list()),
                                      json.loads(result.json))

    def test_list_display_images_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(404, result.status_code)

    def test_get_display_image(self):
        controller = self.create_dummy_display_controller(number_of_images=1)
        image_id = controller.image_store.list()[0].identifier
        result = self.client.get(f"/display/{controller.identifier}/image/{image_id}")
        self.assertEqual(200, result.status_code)
        # TODO: assert on headers
        self.assertEqual(controller.image_store.retrieve(image_id).data, result.data)

    def test_get_display_image_when_image_does_not_exist(self):
        controller = self.create_dummy_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist")
        self.assertEqual(404, result.status_code)


if __name__ == "__main__":
    unittest.main()
