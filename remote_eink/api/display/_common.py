from http import HTTPStatus
from itertools import product
from typing import Callable, Any

from flask import current_app
from marshmallow import Schema, fields
from more_itertools import flatten

from remote_eink.app import APP_ID_PROPERTY
from remote_eink.app_data import apps_data
from remote_eink.controllers.base import DisplayController
from remote_eink.images import ImageType

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


def display_id_handler(wrappable: Callable) -> Callable:
    """
    Converts `displayId` to `display_controller` in the response handler.
    :param wrappable: handler to wrap, where the `displayId` is the first positional or kwarg (with no args)
    :return: handler wrapped in layer to take display ID, validate it and then pass the corresponding display controller
             to the handler
    """

    def wrapped(displayId: str, *args, **kwargs):
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
            return f"Display not found: {displayId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller, *args, **kwargs)

    return wrapped


def display_controllers_handler(wrappable: Callable) -> Callable:
    """
    Injects the app's display controller as `display_controllers` to the callable.
    :param wrappable: function to wrap
    :return: wrapped function
    """

    def wrapped(app_id: str, *args, **kwargs) -> Any:
        app_data = apps_data[app_id]
        kwargs["display_controllers"] = app_data.display_controllers
        return wrappable(*args, **kwargs)

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
