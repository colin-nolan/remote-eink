from http import HTTPStatus

from flask import current_app
from typing import Callable, Any

from bidict import bidict
from marshmallow import Schema, fields

from remote_eink.app import APP_ID_PROPERTY
from remote_eink.app_data import apps_data
from remote_eink.controllers import DisplayController
from remote_eink.images import ImageType

CONTENT_TYPE_HEADER = "Content-Type"

ImageTypeToMimeType = bidict({
    ImageType.BMP: "image/bmp",
    ImageType.JPG: "image/jpeg",
    ImageType.PNG: "image/png",
    ImageType.WEBP: "image/webp"
})
assert set(ImageTypeToMimeType.keys()) == set(ImageType)


class ImageSchema(Schema):
    identifier = fields.Str(data_key="id")


def display_id_handler(wrappable: Callable) -> Callable:
    """
    Handles `displayId` in the response handler.
    :param wrappable: handler to wrap, where the `displayId` is the first positional or kwarg (with no args)
    :return: handler wrapped in layer to take display ID, validate it and then pass the corresponding display controller
             to the handler
    """
    def wrapped(displayId: str, *args, **kwargs):
        app_id = kwargs.pop("app_id")
        try:
            display_controller = apps_data[app_id].display_controllers[displayId]
            assert isinstance(display_controller, DisplayController)
        except KeyError:
            return f"Display not found: {displayId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller, *args, **kwargs)

    return wrapped


def to_target_process(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable:
    :return:
    """
    def unwrapped(*args, **kwargs) -> Any:
        assert kwargs.get("target_process")
        del kwargs["target_process"]
        return wrappable(*args, **kwargs)

    def wrapped(*args, **kwargs) -> Any:
        assert kwargs.get("target_process") is None

        with current_app.app_context():
            app_id = current_app.config[APP_ID_PROPERTY]

        app_data = apps_data[app_id]
        communication_pipe = app_data.communication_pipe

        kwargs["target_process"] = True
        kwargs["app_id"] = app_id
        return communication_pipe.sender.communicate(unwrapped, *args, **kwargs)

    return wrapped


def display_controllers_handler(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable:
    :return:
    """
    def wrapped(app_id: str, *args, **kwargs) -> Any:
        app_data = apps_data[app_id]
        kwargs["display_controllers"] = app_data.display_controllers
        return wrappable(*args, **kwargs)

    return wrapped