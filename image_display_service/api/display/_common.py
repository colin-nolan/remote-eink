from http import HTTPStatus
from typing import Callable

from bidict import bidict
from marshmallow import Schema, fields

from image_display_service.image import ImageType
from image_display_service.web_api import get_display_controllers


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
    :param wrappable: handler to wrap
    :return: handler wrapped in layer to take display ID, validate it and then pass the corresponding display controller
             to the handler
    """
    def wrapped(displayId: str, *args, **kwargs):
        display_controller = get_display_controllers().get(displayId)
        if display_controller is None:
            return f"Display not found: {displayId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller, *args, **kwargs)

    return wrapped
