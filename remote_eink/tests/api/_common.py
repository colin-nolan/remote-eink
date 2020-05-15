import random
from abc import ABCMeta
from typing import Optional, Dict
from uuid import uuid4

from flask_testing import TestCase

from remote_eink.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from remote_eink.display.controllers import DisplayController
from remote_eink.display.drivers import DummyDisplayDriver
from remote_eink.image import ImageType, Image
from remote_eink.storage.image_stores import InMemoryImageStore
from remote_eink.web_api import create_app


def create_image(image_type: Optional[ImageType] = None) -> Image:
    """
    Creates image for testing.
    :return: created image
    """
    if image_type is None:
        image_type = random.choice(list(ImageType))
    identifier = str(uuid4())
    return Image(identifier, lambda: f"data-{identifier}".encode(), image_type)


def create_dummy_display_controller(*, number_of_images: int = 0) -> DisplayController:
    """
    Creates a dummy display controller.
    :param number_of_images: number of images in the display controller's image store
    :return: the dummy display controller
    """
    image_store = InMemoryImageStore(create_image() for _ in range(number_of_images))
    return DisplayController(driver=DummyDisplayDriver(), identifier=str(uuid4()),
                             image_orientation=random.randint(0, 364), image_store=image_store,
                             cycle_images=random.choice([True, False]), cycle_randomly=random.choice([True, False]),
                             cycle_image_after_seconds=random.randint(1, 9999))


def set_content_type_header(image: Image, headers: Optional[Dict] = None):
    """
    Sets content type header for the given image.
    :param image: image to set content type headers for
    :param headers: existing headers to add to (else will create new dict)
    :return: headers
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
