from http import HTTPStatus
from uuid import uuid4

from flask import request

from remote_eink.api.display._common import (
    ImageTypeToMimeType,
    CONTENT_TYPE_HEADER,
    display_id_handler,
    ImageSchema,
    to_target_process,
)
from remote_eink.api.display.image._common import ImageMetadataSchema
from remote_eink.controllers.base import DisplayController
from remote_eink.images import FunctionBasedImage
from remote_eink.storage.image.base import ImageAlreadyExistsError


@to_target_process
@display_id_handler
def search(display_controller: DisplayController):
    images = display_controller.image_store.list()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


def put(*args, **kwargs):
    content_type = request.headers.get(CONTENT_TYPE_HEADER)

    if not content_type.startswith("multipart/form-data"):
        return (
            f"Unsupported content type (expected 'multipart/form-data'): {CONTENT_TYPE_HEADER}",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        data = kwargs["data"]
    except KeyError:
        return (
            f"No data supplied",
            HTTPStatus.BAD_REQUEST,
        )

    content_type = kwargs["data"].content_type
    image_metadata = ImageMetadataSchema().dump(kwargs["body"]["metadata"])
    image_data = data.stream.read()

    # Removing as we've extracted what we wanted from these (keeping them does not help with multiprocessor
    # serialisation!)
    del kwargs["body"]
    del kwargs["data"]

    return _put(*args, **kwargs, data=image_data, content_type=content_type, rotation=image_metadata["rotation"])


def post(*args, **kwargs):
    return put(*args, **kwargs, imageId=str(uuid4()), overwrite=False)


@to_target_process
@display_id_handler
def _put(
    display_controller: DisplayController,
    content_type: str,
    imageId: str,
    data: bytes,
    rotation: float = 0,
    *,
    overwrite: bool = True,
):
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None:
        return (
            f"Unsupported image format: {image_type} (based on content type: {content_type})",
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    image = FunctionBasedImage(imageId, lambda: data, image_type, rotation=rotation)
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
