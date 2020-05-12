import random
from abc import ABCMeta
from typing import Optional, Dict
from uuid import uuid4

from flask_testing import TestCase

from image_display_service.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from image_display_service.display.controllers import DisplayController
from image_display_service.display.drivers import DummyDisplayDriver
from image_display_service.image import ImageType, Image
from image_display_service.storage.image_stores import InMemoryImageStore
from image_display_service.web_api import create_app


def create_image(image_type: Optional[ImageType] = None) -> Image:
    """
    TODO
    :return:
    """
    if image_type is None:
        image_type = random.choice(list(ImageType))
    identifier = str(uuid4())
    return Image(identifier, lambda: f"data-{identifier}".encode(), image_type)


def create_dummy_display_controller(*, number_of_images: int = 0, has_current_image: bool = False) \
        -> DisplayController:
    """
    TODO
    :param number_of_images:
    :param has_current_image:
    :return:
    """
    if has_current_image and number_of_images == 0:
        raise ValueError("Cannot have current images if no images")

    image_store = InMemoryImageStore(create_image() for _ in range(number_of_images))
    current_image = image_store.list()[0] if has_current_image > 0 else None
    return DisplayController(driver=DummyDisplayDriver(), identifier=str(uuid4()), current_image=current_image,
                             image_orientation=random.randint(0, 364), image_store=image_store,
                             cycle_images=random.choice([True, False]), cycle_randomly=random.choice([True, False]),
                             cycle_image_after_seconds=random.randint(1, 9999))


def set_content_type_header(image: Image, headers: Optional[Dict] = None):
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
        controller = create_dummy_display_controller(**kwargs)
        self.display_controllers.append(controller)
        return controller
