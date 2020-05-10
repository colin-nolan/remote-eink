import json
import random
from abc import ABCMeta
from http import HTTPStatus
from typing import Optional, Dict
from uuid import uuid4

from flask_testing import TestCase
import unittest

from image_display_service.api.display._common import ImageTypeToMimeType, CONTENT_TYPE_HEADER
from image_display_service.display.controllers import DisplayController
from image_display_service.display.drivers import DummyDisplayDriver
from image_display_service.image import Image, ImageType
from image_display_service.storage import InMemoryImageStore
from image_display_service.web_api import create_app


def _create_image(image_type: Optional[ImageType] = None) -> Image:
    """
    TODO
    :return:
    """
    if image_type is None:
        image_type = random.choice(list(ImageType))
    identifier = str(uuid4())
    return Image(identifier, lambda: f"data-{identifier}".encode(), image_type)


def _create_dummy_display_controller(*, number_of_images: int = 0, has_current_image: bool = False) \
        -> DisplayController:
    """
    TODO
    :param number_of_images:
    :param has_current_image:
    :return:
    """
    if has_current_image and number_of_images == 0:
        raise ValueError("Cannot have current images if no images")

    image_store = InMemoryImageStore(_create_image() for _ in range(number_of_images))
    current_image = image_store.list()[0] if has_current_image > 0 else None
    return DisplayController(driver=DummyDisplayDriver(), identifier=str(uuid4()), current_image=current_image,
                             image_orientation=random.randint(0, 364), image_store=image_store,
                             cycle_images=random.choice([True, False]), cycle_randomly=random.choice([True, False]),
                             cycle_image_after_seconds=random.randint(1, 9999))


def _set_content_type_header(image: Image, headers: Optional[Dict] = None):
    """
    TODO
    :param image:
    :param headers:
    :return:
    """
    if headers is None:
        headers = {}
    headers[CONTENT_TYPE_HEADER] = ImageTypeToMimeType[image.type]
    return headers


class TestBase(TestCase, metaclass=ABCMeta):
    """
    Base class for tests against the Flask app.
    """
    def create_app(self):
        self.display_controllers = []
        app = create_app(self.display_controllers).app
        app.config["TESTING"] = True
        return app

    def create_dummy_display_controller(self, **kwargs) -> DisplayController:
        controller = _create_dummy_display_controller(**kwargs)
        self.display_controllers.append(controller)
        return controller


class TestDisplayApi(TestBase):
    """
    Tests for the `/display` endpoint.
    """
    def test_list(self):
        display_controllers = [self.create_dummy_display_controller() for _ in range(10)]
        result = self.client.get("/display")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertCountEqual([{"id": controller.identifier} for controller in display_controllers], result.json)

    def test_get(self):
        for _ in range(5):
            self.create_dummy_display_controller()
        controller = self.create_dummy_display_controller(number_of_images=10, has_current_image=True)
        for _ in range(5):
            self.create_dummy_display_controller()

        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(controller.identifier, result.json["id"])
        self.assertEqual(controller.current_image.identifier, result.json["currentImage"]["id"])
        self.assertCountEqual((image.identifier for image in controller.image_store.list()),
                              (image["id"] for image in result.json["images"]))
        self.assertEqual(controller.image_orientation, result.json["orientation"])
        self.assertEqual(controller.cycle_images, result.json["cycleImages"])
        self.assertEqual(controller.cycle_images_randomly, result.json["cycleRandomly"])
        self.assertEqual(controller.cycle_image_after_seconds, result.json["cycleAfterSeconds"])

    def test_get_not_exist(self):
        result = self.client.get(f"/display/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_with_no_images(self):
        controller = self.create_dummy_display_controller(number_of_images=0)
        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual([], result.json["images"])
        self.assertIsNone(result.json["currentImage"])


class TestDisplayImage(TestBase):
    """
    Tests for the `/display/{displayId}/image` endpoint.
    """
    def test_list(self):
        for number_of_images in range(5):
            with self.subTest(number_of_images=number_of_images):
                controller = self.create_dummy_display_controller(number_of_images=number_of_images)
                result = self.client.get(f"/display/{controller.identifier}/image")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertCountEqual(({"id": image.identifier} for image in controller.image_store.list()),
                                      result.json)

    def test_list_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_image(self):
        for image_type in ImageType:
            with self.subTest(image_type=image_type.name):
                controller = self.create_dummy_display_controller()
                image = _create_image(image_type)
                controller.image_store.save(image)
                result = self.client.get(f"/display/{controller.identifier}/image/{image.identifier}")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertEqual(ImageTypeToMimeType[image_type], result.mimetype)
                self.assertEqual(controller.image_store.retrieve(image.identifier).data, result.data)

    def test_get_when_does_not_exist(self):
        controller = self.create_dummy_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_save(self):
        controller = self.create_dummy_display_controller()
        image = _create_image()
        result = self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data,
                                  headers=_set_content_type_header(image))
        self.assertEqual(HTTPStatus.CREATED, result.status_code)

    def test_save_with_duplicate_id(self):
        controller = self.create_dummy_display_controller()
        image_1 = _create_image()
        self.client.post(f"/display/{controller.identifier}/image/{image_1.identifier}", data=image_1.data,
                         headers=_set_content_type_header(image_1))
        image_2 = _create_image()
        result = self.client.post(f"/display/{controller.identifier}/image/{image_1.identifier}", data=image_2.data,
                                  headers=_set_content_type_header(image_2))
        self.assertEqual(HTTPStatus.CONFLICT, result.status_code)

    def test_save_no_content_type_header(self):
        controller = self.create_dummy_display_controller()
        image = _create_image()
        result = self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data)
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_save_display_not_exist(self):
        image = _create_image()
        result = self.client.post(f"/display/does-not-exist/image/{image.identifier}", data=image.data)
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image(self):
        controller = self.create_dummy_display_controller()
        image = _create_image()
        self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data,
                         headers=_set_content_type_header(image))
        result = self.client.delete(f"/display/{controller.identifier}/image/{image.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)

    def test_delete_image_does_not_exist(self):
        controller = self.create_dummy_display_controller()
        result = self.client.delete(f"/display/{controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image_display_does_not_exist(self):
        result = self.client.delete(f"/display/does-not-exist/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)


if __name__ == "__main__":
    unittest.main()
