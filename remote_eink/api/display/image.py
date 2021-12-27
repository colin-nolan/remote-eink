import io
from http import HTTPStatus
from uuid import uuid4

from typing import Optional, Tuple

from io import BytesIO

from flask import make_response, request, send_file

from remote_eink.api.display._common import (
    ImageTypeToMimeType,
    CONTENT_TYPE_HEADER,
    display_id_handler,
    ImageSchema,
    to_target_process,
)
from remote_eink.controllers import DisplayController
from remote_eink.images import FunctionBasedImage
from remote_eink.storage.images import ImageAlreadyExistsError

try:
    from PIL import Image, UnidentifiedImageError

    _HAS_IMAGE_TOOLS = True
except ImportError:
    _HAS_IMAGE_TOOLS = False


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


def put(*args, **kwargs):
    kwargs["content_type"] = request.headers.get(CONTENT_TYPE_HEADER)
    return _put(*args, **kwargs, overwrite=True)


def post(*args, **kwargs):
    print(request.stream.read())
    content_type = request.headers.get(CONTENT_TYPE_HEADER)

    if content_type.startswith("multipart/form-data"):
        kwargs["image_data"] = kwargs["body"]["image"]
        kwargs["content_type"] = kwargs["body"]["image"]
        kwargs["rotation"] = kwargs["body"]["metadata"]["rotation"]
    else:
        kwargs["image_data"] = kwargs["body"]
        kwargs["content_type"] = content_type

    del kwargs["body"]

    kwargs["content_type"] = content_type
    return _put(*args, **kwargs, imageId=str(uuid4()), overwrite=False)


@to_target_process
@display_id_handler
def _put(
    display_controller: DisplayController,
    content_type: str,
    imageId: str,
    body: bytes,
    rotation: float = 0,
    *,
    overwrite: bool,
):
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None and _HAS_IMAGE_TOOLS:
        # Attempt to identify image type automatically
        try:
            image_mime = Image.MIME[Image.open(io.BytesIO(body)).format]
            image_type = ImageTypeToMimeType.inverse.get(image_mime)
        except UnidentifiedImageError:
            pass
    if image_type is None:
        return (
            f"Unsupported image format: {image_type} (based on content type: {content_type})",
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    image = FunctionBasedImage(imageId, lambda: image_data, image_type, rotation=rotation)
    updated = False
    # FIXME: lock over both of these is required!
    if overwrite:
        updated = display_controller.image_store.remove(image.identifier)
    try:
        display_controller.image_store.add(image)
    except ImageAlreadyExistsError:
        return f"Image with same ID already exists: {imageId}", HTTPStatus.CONFLICT

    return imageId, HTTPStatus.CREATED if not updated else HTTPStatus.OK


@to_target_process
@display_id_handler
def delete(display_controller: DisplayController, imageId: str):
    deleted = display_controller.image_store.remove(imageId)
    if not deleted:
        return f"Image not found: {imageId}", HTTPStatus.NOT_FOUND
    return f"Deleted: {imageId}", HTTPStatus.OK
