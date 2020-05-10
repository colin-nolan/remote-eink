from http import HTTPStatus
from typing import Tuple, Callable

from bidict import bidict
from flask import make_response, Response, request

from image_display_service.display.controllers import DisplayController
from image_display_service.image import ImageType, Image
from image_display_service.storage import ImageAlreadyExistsError
from image_display_service.web_api import get_display_controllers
from marshmallow import Schema, fields

CONTENT_TYPE_HEADER = "Content-Type"


ImageTypeToMimeType = bidict({
    ImageType.BMP: "image/bmp",
    ImageType.JPG: "image/jpeg",
    ImageType.PNG: "image/png",
    ImageType.WEBP: "image/webp"
})
assert set(ImageTypeToMimeType.keys()) == set(ImageType)


class _ImageSchema(Schema):
    identifier = fields.Str(data_key="id")


class _DisplayControllerSchema(Schema):
    identifier = fields.Str(data_key="id")
    current_image = fields.Nested(_ImageSchema, only=["identifier"], data_key="currentImage")
    images = fields.Function(lambda display_controller: _ImageSchema(only=["identifier"]).dump(
        display_controller.image_store.list(), many=True))
    image_orientation = fields.Integer(data_key="orientation")
    cycle_images = fields.Bool(data_key="cycleImages")
    cycle_images_randomly = fields.Bool(data_key="cycleRandomly")
    cycle_image_after_seconds = fields.Integer(data_key="cycleAfterSeconds")


def _display_id_handler(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable:
    :return:
    """
    def wrapped(displayId: str, *args, **kwargs):
        display_controller = get_display_controllers().get(displayId)
        if display_controller is None:
            return f"Display not found: {displayId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller, *args, **kwargs)

    return wrapped


def search():
    return _DisplayControllerSchema(only=["identifier"], many=True).dump(get_display_controllers().values()), \
           HTTPStatus.OK


@_display_id_handler
def get(display_controller: DisplayController):
    return _DisplayControllerSchema().dump(display_controller), HTTPStatus.OK


@_display_id_handler
def image_search(display_controller: DisplayController):
    images = display_controller.image_store.list()
    return _ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


@_display_id_handler
def image_get(display_controller: DisplayController, imageId: str):
    image = display_controller.image_store.retrieve(imageId)

    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    response = make_response(image.data, HTTPStatus.OK)
    response.headers[CONTENT_TYPE_HEADER] = ImageTypeToMimeType[image.type]
    return response


@_display_id_handler
def image_post(display_controller: DisplayController, imageId: str, body: bytes):
    content_type = request.headers.get(CONTENT_TYPE_HEADER)
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None:
        return f"Unsupported image format: {image_type}", HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    image = Image(imageId, lambda: body, image_type)
    try:
        display_controller.image_store.save(image)
    except ImageAlreadyExistsError:
        return f"Image with same ID already exists: {imageId}", HTTPStatus.CONFLICT

    return f"Created {imageId}", HTTPStatus.CREATED


@_display_id_handler
def image_delete(display_controller: DisplayController, imageId: str):
    deleted = display_controller.image_store.delete(imageId)
    if not deleted:
        return f"Image not found: {imageId}", HTTPStatus.NOT_FOUND
    return f"Deleted: {imageId}", HTTPStatus.OK
