from http import HTTPStatus
from io import BytesIO
from typing import Optional, Tuple

from flask import make_response, send_file, request

from remote_eink.api.display._common import (
    ImageTypeToMimeType,
    display_id_handler,
    to_target_process, CONTENT_TYPE_HEADER,
)
from remote_eink.controllers.base import DisplayController


def search(displayId: str, imageId: str, *args, **kwargs):
    result = _get_data(displayId, imageId, *args, **kwargs)
    if result is None:
        # `make_response` must be ran in the thread handling the response
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return send_file(*result)


# @to_target_process
# @display_id_handler
def put(body: bytes, **kwargs):
    kwargs["content_type"] = request.headers.get(CONTENT_TYPE_HEADER)
    pass


@to_target_process
@display_id_handler
def _get_data(display_controller: DisplayController, image_id: str) -> Optional[Tuple[BytesIO, str]]:
    image = display_controller.image_store.get(image_id)

    if image is None:
        return None

    return BytesIO(image.data), ImageTypeToMimeType[image.type]
