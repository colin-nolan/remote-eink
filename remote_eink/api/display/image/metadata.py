from http import HTTPStatus
from typing import Dict

from flask import make_response

from remote_eink.api.display._common import (
    display_id_handler,
    to_target_process,
)
from remote_eink.api.display.image._common import get_image
from remote_eink.controllers.base import DisplayController


def search(*, imageId: str, **kwargs):
    image = get_image(image_id=imageId, **kwargs)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return image.metadata, HTTPStatus.OK


@to_target_process
@display_id_handler
def put(display_controller: DisplayController, imageId: str, body: Dict):
    image = display_controller.image_store.get(imageId)
    if image is None:
        return make_response(f"Cannot put metadata as image does not exist: {imageId}", HTTPStatus.NOT_FOUND)

    display_controller.image_store.add(image)
