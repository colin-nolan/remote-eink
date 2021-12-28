from http import HTTPStatus
from io import BytesIO
from typing import Optional, Tuple

from flask import make_response, send_file

from remote_eink.api.display._common import (
    ImageTypeToMimeType,
    display_id_handler,
    to_target_process,
)
from remote_eink.controllers import DisplayController


def search(displayId: str, imageId: str, *args, **kwargs):
    result = _get_data(displayId, imageId, *args, **kwargs)
    if result is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return send_file(*result)


@to_target_process
@display_id_handler
def _get_data(display_controller: DisplayController, imageId: str) -> Optional[Tuple[BytesIO, str]]:
    image = display_controller.image_store.get(imageId)

    if image is None:
        return None

    return BytesIO(image.data), ImageTypeToMimeType[image.type]
