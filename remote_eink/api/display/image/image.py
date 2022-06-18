from http import HTTPStatus
from uuid import uuid4

from flask import request

from remote_eink.api.display._common import (
    CONTENT_TYPE_HEADER,
    display_id_handler,
    ImageSchema,
    to_target_process,
)
from remote_eink.api.display.image._common import put_image
from remote_eink.controllers.base import DisplayController



@to_target_process
@display_id_handler
def search(display_controller: DisplayController):
    images = display_controller.image_store.list()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


def put(*args, **kwargs):
    content_type = request.headers.get(CONTENT_TYPE_HEADER)

    if content_type is None or not content_type.startswith("multipart/form-data"):
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
    image_metadata = kwargs["body"]["metadata"]
    image_data = data.stream.read()

    # Removing as we've extracted what we wanted from these (keeping them does not help with multiprocessor
    # serialisation!)
    del kwargs["body"]
    del kwargs["data"]

    extras = {}
    if "rotation" in image_metadata:
        extras["rotation"] = image_metadata["rotation"]

    return put_image(*args, **kwargs, data=image_data, content_type=content_type, **extras)


def post(*args, **kwargs):
    return put(*args, **kwargs, imageId=str(uuid4()), overwrite=False)


@to_target_process
@display_id_handler
def delete(display_controller: DisplayController, imageId: str):
    deleted = display_controller.image_store.remove(imageId)
    if not deleted:
        return f"Image not found: {imageId}", HTTPStatus.NOT_FOUND
    return f"Deleted: {imageId}", HTTPStatus.OK
