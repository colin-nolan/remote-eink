import random
from contextlib import contextmanager

from abc import ABCMeta
from typing import Optional, Dict, Any, Callable, ContextManager
from uuid import uuid4

from flask_testing import TestCase

from remote_eink.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from remote_eink.app_storage import NonSynchronisedAppStorage
from remote_eink.display.controllers import DisplayController
from remote_eink.display.drivers import DummyDisplayDriver
from remote_eink.models import ImageType, Image
from remote_eink.storage.images import InMemoryImageStore
from remote_eink.app import create_app, get_app_storage, destroy_app
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


def create_dummy_display_controller(*, number_of_images: int = 0, number_of_image_transformers: int = 0, **kwargs) \
        -> DisplayController:
    """
    Creates a dummy display controller.
    :param number_of_images: number of images in the display controller's image store
    :param number_of_image_transformers: number of image transformers to create
    :param kwargs: key-word arguments to pass to `DisplayController`
    :return: the dummy display controller
    """
    if number_of_images != 0 and "image_store" in kwargs:
        raise ValueError("Cannot specify number of images to create in an image store and pass in image store")
    if "image_store" not in kwargs:
        kwargs["image_store"] = InMemoryImageStore(create_image() for _ in range(number_of_images))

    if number_of_image_transformers != 0:
        if "image_transformers" in kwargs:
            raise ValueError("Cannot specify a number of image transformers to be created in addition to passing in "
                             "image transformers")
        kwargs["image_transformers"] = [DummyImageTransformer() for _ in range(number_of_image_transformers)]

    return DisplayController(driver=DummyDisplayDriver(), **kwargs)


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
    @property
    def display_controller(self) -> DisplayController:
        return self._display_controllers[0]

    @property
    def display_controllers(self) -> Dict[str, DisplayController]:
        return {x.identifier: x for x in self._display_controllers}

    def tearDown(self):
        if self._app:
            destroy_app(self._app)

    # Required to satisfy the super class' interface
    def create_app(self):
        self._display_controllers = []
        # Note: use of `NonSynchronisedAppStorage` makes the tests a lot faster
        self._app = create_app(self._display_controllers, NonSynchronisedAppStorage).app
        self._app.config["TESTING"] = True
        return self._app

    def create_display_controller(self, **kwargs):
        display_controller = create_dummy_display_controller(**kwargs)
        with get_app_storage(app=self._app).update_display_controllers() as display_controllers:
            display_controllers[display_controller.identifier] = display_controller
        self._display_controllers.append(display_controller)
        return display_controller

    @contextmanager
    def create_and_update_display_controller(self, **kwargs) -> ContextManager[DisplayController]:
        display_controller = create_dummy_display_controller(**kwargs)
        self._display_controllers.append(display_controller)
        try:
            yield display_controller
        finally:
            with get_app_storage(app=self._app).update_display_controllers() as display_controllers:
                display_controllers[display_controller.identifier] = display_controller

    def synchronise_display_controllers(self):
        self._display_controllers = list(get_app_storage(app=self._app).display_controllers.values())


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