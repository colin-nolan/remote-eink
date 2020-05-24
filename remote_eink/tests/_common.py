import random
from abc import ABCMeta
from typing import Optional, Dict, Any, Callable
from uuid import uuid4

from flask_testing import TestCase

from remote_eink.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from remote_eink.display.controllers import DisplayController
from remote_eink.display.drivers import DummyDisplayDriver
from remote_eink.models import ImageType, Image
from remote_eink.storage.images import InMemoryImageStore
from remote_eink.app import create_app
from remote_eink.transformers import ImageTransformer
from remote_eink.transformers.transformers import InvalidConfigurationError


def create_image(image_type: Optional[ImageType] = None) -> Image:
    """
    Creates image for testing.
    :return: created image
    """
    if image_type is None:
        image_type = random.choice(list(ImageType))
    identifier = str(uuid4())
    return Image(identifier, lambda: f"data-{identifier}".encode(), image_type)


def create_dummy_display_controller(*, number_of_images: int = 0, **kwargs) -> DisplayController:
    """
    Creates a dummy display controller.
    :param number_of_images: number of images in the display controller's image store
    :param kwargs: key-word arguments to pass to `DisplayController`
    :return: the dummy display controller
    """
    image_store = InMemoryImageStore(create_image() for _ in range(number_of_images))
    return DisplayController(driver=DummyDisplayDriver(), image_store=image_store, **kwargs)


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


class AppTestBase(TestCase, metaclass=ABCMeta):
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


class DummyImageTransformer(ImageTransformer):
    @property
    def configuration(self) -> Dict[str, Any]:
        return self.dummy_configuration

    @property
    def description(self) -> str:
        return self.dummy_description

    def __init__(self, transformer: Optional[Callable[[Image], Image]] = None, active: bool = True,
                 configuration: Optional[Any] = None, description: Optional[str] = None, identifier: str = None):
        super().__init__(identifier if identifier is not None else str(uuid4()), active)
        self.dummy_transformer = transformer if transformer is not None else lambda image: image
        self.dummy_configuration = configuration if configuration is not None else {}
        self.dummy_description = description if description is not None else ""

    def modify_configuration(self, configuration: Dict[str, Any]):
        if "invalid-config-property" in configuration:
            raise InvalidConfigurationError(configuration)
        self.dummy_configuration = configuration

    def _transform(self, image: Image) -> Image:
        return self.dummy_transformer(image)