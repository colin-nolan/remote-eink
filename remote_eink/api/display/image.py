from http import HTTPStatus
from typing import Optional, Tuple

from io import BytesIO

from flask import make_response, request, send_file

from remote_eink.api.display._common import ImageTypeToMimeType, CONTENT_TYPE_HEADER, display_id_handler, ImageSchema, \
    to_target_process
from remote_eink.controllers import DisplayController
from remote_eink.images import FunctionBasedImage
from remote_eink.storage.images import ImageAlreadyExistsError


@to_target_process
@display_id_handler
def search(display_controller: DisplayController):
    images = display_controller.image_store.list()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


def get(displayId: str, imageId: str, *args, **kwargs):
    result = _get(displayId, imageId, *args, **kwargs)
    if result is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return send_file(*result)


@to_target_process
@display_id_handler
def _get(display_controller: DisplayController, imageId: str) -> Optional[Tuple[BytesIO, str]]:
    image = display_controller.image_store.get(imageId)

    if image is None:
        return None

    return BytesIO(image.data), ImageTypeToMimeType[image.type]


def post(*args, **kwargs):
    kwargs["content_type"] = request.headers.get(CONTENT_TYPE_HEADER)
    return _post(*args, **kwargs)


@to_target_process
@display_id_handler
def _post(display_controller: DisplayController, content_type: str, imageId: str, body: bytes) \
        -> Tuple[str, HTTPStatus]:
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None:
        return f"Unsupported image format: {image_type}", HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    image = FunctionBasedImage(imageId, lambda: body, image_type)
    try:
        display_controller.image_store.add(image)
    except ImageAlreadyExistsError:
        return f"Image with same ID already exists: {imageId}", HTTPStatus.CONFLICT

    return f"Created {imageId}", HTTPStatus.CREATED


@to_target_process
@display_id_handler
def delete(display_controller: DisplayController, imageId: str):
    deleted = display_controller.image_store.remove(imageId)
    if not deleted:
        return f"Image not found: {imageId}", HTTPStatus.NOT_FOUND
    return f"Deleted: {imageId}", HTTPStatus.OK
