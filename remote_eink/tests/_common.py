import random

from multiprocessing_on_dill.connection import Pipe

from abc import ABCMeta
from flask_testing import TestCase
from multiprocessing_on_dill.context import Process
from typing import Optional, Dict, Callable, Any
from uuid import uuid4

from remote_eink.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from remote_eink.app import create_app, destroy_app, get_app_data
from remote_eink.app_data import AppData
from remote_eink.controllers.base import DisplayController
from remote_eink.controllers.simple import SimpleDisplayController
from remote_eink.images import ImageType, Image, FunctionBasedImage
from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.drivers._common import DummyBaseDisplayDriver
from remote_eink.tests.storage._common import WHITE_IMAGE
from remote_eink.transformers.simple import SimpleImageTransformer


def create_image(**kwargs) -> Image:
    """
    Creates image for testing.
    :return: created image
    """
    if "image_type" not in kwargs:
        kwargs["image_type"] = random.choice(list(ImageType))
    identifier = str(uuid4())
    return FunctionBasedImage(identifier, lambda: WHITE_IMAGE.data, **kwargs)


def create_dummy_display_controller(
    *, number_of_images: int = 0, number_of_image_transformers: int = 0, **kwargs
) -> DisplayController:
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
            raise ValueError(
                "Cannot specify a number of image transformers to be created in addition to passing in "
                "image transformers"
            )
        kwargs["image_transformers"] = [SimpleImageTransformer() for _ in range(number_of_image_transformers)]

    return SimpleDisplayController(driver=DummyBaseDisplayDriver(), **kwargs)


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

    @property
    def app_data(self) -> AppData:
        return get_app_data(self.app)

    def setUp(self):
        self._display_controllers.append(self.create_display_controller())

    def tearDown(self):
        if self._app:
            destroy_app(self._app)

    # Required to satisfy the super class' interface
    def create_app(self):
        self._display_controllers = []
        self._app = create_app(self._display_controllers)
        return self._app

    def create_display_controller(self, **kwargs):
        display_controller = create_dummy_display_controller(**kwargs)
        get_app_data(self._app).add_display_controller(display_controller)
        self._display_controllers.append(display_controller)
        return display_controller


def run_in_different_process(callable: Callable, *args, **kwargs) -> Any:
    """
    Runs the given callable and arguments/keyword arguments in a different process and resturn the result.
    :param callable: callable to run
    :return: result from callable (moved over Pipe)
    """
    parent, child = Pipe()

    def wrapped():
        nonlocal child, callable, args, kwargs
        try:
            raised, value = False, callable(*args, **kwargs)
        except Exception as e:
            raised, value = True, e
        child.send((raised, value))

    process = Process(target=wrapped)
    process.start()
    raised, value = parent.recv()
    if raised:
        raise value
    process.join(timeout=15)
    if process.exitcode != 0:
        raise RuntimeError(f"Process exited with non-zero error code {process.exitcode}: {callable}, {args}, {kwargs}")
    return value
