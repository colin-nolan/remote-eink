from http import HTTPStatus
from typing import Optional, Dict

from flask import make_response

from remote_eink.api.display._common import (
    display_id_handler,
    to_target_process,
)
from remote_eink.controllers.base import DisplayController
from remote_eink.images import Image


def search(*, imageId: str, **kwargs):
    image = _get_metadata(image_id=imageId, **kwargs)
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


@to_target_process
@display_id_handler
def _get_metadata(display_controller: DisplayController, image_id: str) -> Optional[Image]:
    return display_controller.image_store.get(image_id)
