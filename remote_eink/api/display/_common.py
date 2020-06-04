from http import HTTPStatus
from typing import Callable

from bidict import bidict
from marshmallow import Schema, fields

from remote_eink.app import get_display_controller
from remote_eink.controllers import DisplayController
from remote_eink.models import ImageType

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
        try:
            display_controller = get_display_controller(displayId)
            assert isinstance(display_controller, DisplayController)
        except KeyError:
            return f"Display not found: {displayId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller, *args, **kwargs)

    return wrapped
