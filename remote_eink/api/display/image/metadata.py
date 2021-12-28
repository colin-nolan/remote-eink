from http import HTTPStatus
from typing import Optional

from flask import make_response

from remote_eink.api.display._common import (
    display_id_handler,
    to_target_process,
)
from remote_eink.api.display.image._common import ImageMetadataSchema
from remote_eink.controllers.base import DisplayController
from remote_eink.images import Image


def search(*, imageId: str, **kwargs):
    image = _get_metadata(image_id=imageId, **kwargs)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return ImageMetadataSchema().dump(image), HTTPStatus.OK


@to_target_process
@display_id_handler
def _get_metadata(display_controller: DisplayController, image_id: str) -> Optional[Image]:
    return display_controller.image_store.get(image_id)
