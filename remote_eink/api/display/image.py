from http import HTTPStatus

from flask import make_response, request

from remote_eink.api.display._common import ImageTypeToMimeType, CONTENT_TYPE_HEADER, display_id_handler, ImageSchema
from remote_eink.display.controllers import DisplayController
from remote_eink.models import Image
from remote_eink.storage.images import ImageAlreadyExistsError


@display_id_handler
def search(display_controller: DisplayController):
    images = display_controller.image_store.list()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


@display_id_handler
def get(display_controller: DisplayController, imageId: str):
    image = display_controller.image_store.get(imageId)

    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    response = make_response(image.data, HTTPStatus.OK)
    response.headers[CONTENT_TYPE_HEADER] = ImageTypeToMimeType[image.type]
    return response


@display_id_handler
def post(display_controller: DisplayController, imageId: str, body: bytes):
    content_type = request.headers.get(CONTENT_TYPE_HEADER)
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None:
        return f"Unsupported image format: {image_type}", HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    image = Image(imageId, lambda: body, image_type)
    try:
        display_controller.image_store.add(image)
    except ImageAlreadyExistsError:
        return f"Image with same ID already exists: {imageId}", HTTPStatus.CONFLICT

    return f"Created {imageId}", HTTPStatus.CREATED


@display_id_handler
def delete(display_controller: DisplayController, imageId: str):
    deleted = display_controller.image_store.remove(imageId)
    if not deleted:
        return f"Image not found: {imageId}", HTTPStatus.NOT_FOUND
    return f"Deleted: {imageId}", HTTPStatus.OK
