from http import HTTPStatus
from itertools import product
from typing import Callable, Any, Optional, Iterator, List, Union

from flask import current_app, make_response
from marshmallow import Schema, fields
from more_itertools import flatten

from remote_eink.app import APP_ID_PROPERTY
from remote_eink.app_data import apps_data
from remote_eink.controllers.base import DisplayController
from remote_eink.drivers.base import DisplayDriver
from remote_eink.images import ImageType, Image
from remote_eink.storage.image.base import ImageStore
from remote_eink.transformers import ImageTransformerSequence, ImageTransformer

CONTENT_TYPE_HEADER = "Content-Type"

ImageTypeToMimeTypes = {
    ImageType.BMP: ("image/bmp",),
    ImageType.JPG: ("image/jpeg", "image/jpg"),
    ImageType.PNG: ("image/png",),
    ImageType.WEBP: ("image/webp",),
}
MimeTypeToImageType = dict(flatten(product(v, (k,)) for k, v in ImageTypeToMimeTypes.items()))


class ImageSchema(Schema):
    identifier = fields.Str(data_key="id")


class DisplayControllerNotFoundError(RuntimeError):
    def __init__(self, display_id: str):
        self.display_id = display_id
        super().__init__(f"Display controller not found: {display_id}")


def handle_display_controller_not_found_response(wrappable: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        try:
            return wrappable(*args, **kwargs)
        except DisplayControllerNotFoundError as e:
            return make_response(f"Display not found: {e.display_id}", HTTPStatus.NOT_FOUND)

    return wrapped


def to_target_process(wrappable: Callable) -> Callable:
    """
    Wraps the given callable and arranges for it be executed on the "target" process (that which instantiated `AppData`
    and is listening to requests on a `CommunicationPipe`).
    :param wrappable: function to wrap
    :return: wrapped function
    :raises AssertionError: if called on the target process
    """

    def unwrapped(*args, **kwargs) -> Any:
        assert kwargs.get("target_process")
        del kwargs["target_process"]
        return wrappable(*args, **kwargs)

    def wrapped(*args, **kwargs) -> Any:
        if kwargs.get("target_process") is not None:
            raise AssertionError("Wrapped callable is already executing on target process")
        with current_app.app_context():
            app_id = current_app.config[APP_ID_PROPERTY]
        kwargs["target_process"] = True
        kwargs["app_id"] = app_id
        return _on_target_process(unwrapped, *args, **kwargs)

    return wrapped


def _on_target_process(callable: Callable, *args, **kwargs) -> Any:
    """
    Executes the given callable it on the "target" process (that which instantiated `AppData` and is  listening to
    requests on a `CommunicationPipe`).
    :param callable: callable to execute on target process
    :return: return from the target process
    """
    with current_app.app_context():
        app_id = current_app.config[APP_ID_PROPERTY]

    app_data = apps_data[app_id]
    communication_pipe = app_data.communication_pipe

    return communication_pipe.sender.communicate(callable, *args, **kwargs)


def _display_id_handler(wrappable: Callable) -> Callable:
    """
    Converts `displayId` to `display_controller` in the response handler.
    :param wrappable: handler to wrap, where the `displayId` is the first positional or kwarg (with no args)
    :return: handler wrapped in layer to take display ID, validate it and then pass the corresponding display controller
             to the handler
    """

    def wrapped(*args, displayId: str, **kwargs):
        try:
            app_id = kwargs.pop("app_id")
        except KeyError as e:
            raise AssertionError(
                "Expected `app_id` data (is the annotation placed _after_ `to_target_process`?)"
            ) from e
        try:
            display_controller = apps_data[app_id].display_controllers[displayId]
            if not isinstance(display_controller, DisplayController):
                raise AssertionError("Unexpected type of display controller")
        except KeyError:
            raise DisplayControllerNotFoundError(displayId)
        assert "display_controller" not in kwargs
        return wrappable(*args, display_controller=display_controller, **kwargs)

    return wrapped


def _add_display_id(wrappable: Callable) -> Callable:
    def wrapped(remote_thread_base: "RemoteThreadBase", *args, **kwargs):
        return wrappable(remote_thread_base, *args, displayId=remote_thread_base.display_id, **kwargs)

    return wrapped


class RemoteThreadBase:
    def __init__(self, display_id: str, remote_object_factory: Callable[[DisplayController], Any]):
        self.display_id = display_id
        self._remote_object_factory = remote_object_factory

    @to_target_process
    @_add_display_id
    @_display_id_handler
    def _call_on_remote(self, method, *args, display_controller: DisplayController, **kwargs) -> Any:
        assert isinstance(display_controller, DisplayController)
        return getattr(self._remote_object_factory(display_controller), method)(*args, **kwargs)

    @to_target_process
    @_add_display_id
    @_display_id_handler
    def _set_on_remote(self, property_name: str, value: Any, display_controller: DisplayController) -> Any:
        assert isinstance(display_controller, DisplayController)
        return setattr(self._remote_object_factory(display_controller), property_name, value)

    @to_target_process
    @_add_display_id
    @_display_id_handler
    def _read_on_remote(self, property_name: str, display_controller: DisplayController) -> Any:
        assert isinstance(display_controller, DisplayController)
        return getattr(self._remote_object_factory(display_controller), property_name)


class RemoteThreadDisplayController(DisplayController, RemoteThreadBase):
    @property
    def friendly_type_name(self) -> str:
        return self._read_on_remote("friendly_type_name")

    @property
    def identifier(self) -> str:
        return self._read_on_remote("identifier")

    @property
    def current_image(self) -> Optional[Image]:
        return self._read_on_remote("current_image")

    @property
    def driver(self) -> DisplayDriver:
        return RemoteThreadDisplayDriver(self.display_id)

    @property
    def image_store(self) -> ImageStore:
        return RemoteThreadImageStore(self.display_id)

    @property
    def image_transformers(self) -> ImageTransformerSequence:
        return self._read_on_remote("image_transformers")

    def __init__(self, display_id: str):
        super().__init__(display_id, lambda display_controller: display_controller)

    def display(self, image_id: str):
        return self._call_on_remote("display", image_id)

    def clear(self):
        return self._call_on_remote("clear")

    def apply_image_transforms(self, image: Image) -> Image:
        return self._call_on_remote("apply_image_transforms", image)


class RemoteThreadImageStore(ImageStore, RemoteThreadBase):
    @property
    def friendly_type_name(self) -> str:
        return self._read_on_remote("friendly_type_name")

    def __init__(self, display_id: str):
        super().__init__(display_id, lambda display_controller: display_controller.image_store)

    def __len__(self) -> int:
        return self._call_on_remote("__len__")

    def __iter__(self) -> Iterator[Image]:
        return self._call_on_remote("__iter__")

    def __contains__(self, __x: object) -> bool:
        return self._call_on_remote("__contains__")

    def get(self, image_id: str) -> Optional[Image]:
        return self._call_on_remote("get", image_id)

    def list(self) -> List[Image]:
        return self._call_on_remote("list")

    def add(self, image: Image):
        return self._call_on_remote("add", image)

    def remove(self, image_id: str) -> bool:
        return self._call_on_remote("remove", image_id)


class RemoteThreadDisplayDriver(DisplayDriver, RemoteThreadBase):
    @property
    def sleeping(self) -> bool:
        return self._read_on_remote("sleeping")

    @property
    def image(self) -> Optional[Image]:
        return self._read_on_remote("image")

    def __init__(self, display_id: str):
        super().__init__(display_id, lambda display_controller: display_controller.driver)

    def sleep(self):
        return self._call_on_remote("sleep")

    def wake(self):
        return self._call_on_remote("wake")


class RemoteThreadImageTransformerSequence(ImageTransformerSequence, RemoteThreadBase):
    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        transformer = self._call_on_remote("get_by_id", image_transformer_id)
        if transformer is None:
            return None
        return RemoteThreadImageTransformer(self.display_id, transformer.identifier)

    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        return self._call_on_remote("get_position", image_transformer)

    def set_position(self, image_transformer: str, position: int):
        return self._call_on_remote("set_position", image_transformer, position)

    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        return self._call_on_remote("add", image_transformer, position)

    def remove(self, image_transformer: ImageTransformer) -> bool:
        return self._call_on_remote("remove", image_transformer)

    def __init__(self, display_id: str):
        super().__init__(display_id, lambda display_controller: display_controller.image_transformers)

    def __getitem__(self, i: int) -> ImageTransformer:
        transformer = self._call_on_remote("__getitem__", i)
        return RemoteThreadImageTransformer(self.display_id, transformer.identifier)

    def __len__(self) -> int:
        return self._call_on_remote("__len__")


class RemoteThreadImageTransformer(ImageTransformer, RemoteThreadBase):
    @property
    def active(self) -> bool:
        return self._read_on_remote("active")

    @active.setter
    def active(self, active: bool):
        self._set_on_remote("active", active)

    @property
    def configuration(self) -> dict[str, Any]:
        return self._read_on_remote("configuration")

    @property
    def description(self) -> str:
        return self._read_on_remote("description")

    @property
    def identifier(self) -> str:
        return self._read_on_remote("identifier")

    def modify_configuration(self, configuration: dict[str, Any]):
        return self._call_on_remote("modify_configuration", configuration)

    def transform(self, image: Image) -> Image:
        return self._call_on_remote("transform", image)

    def __init__(self, display_id: str, image_transformer_id: str):
        super().__init__(
            display_id,
            lambda display_controller: display_controller.image_transformers.get_by_id(image_transformer_id),
        )
