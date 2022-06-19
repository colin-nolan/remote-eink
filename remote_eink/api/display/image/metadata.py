from http import HTTPStatus
from typing import Dict

from flask import make_response

from remote_eink.api.display._common import (
    RemoteThreadImageStore,
    handle_display_controller_not_found_response,
)


@handle_display_controller_not_found_response
def search(imageId: str, displayId: str):
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return image.metadata, HTTPStatus.OK


@handle_display_controller_not_found_response
def put(imageId: str, displayId: str, body: Dict):
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Cannot put metadata as image does not exist: {imageId}", HTTPStatus.NOT_FOUND)

    # display_controller.image_store.add(image)
    # FIXME: implement!
