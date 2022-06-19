from http import HTTPStatus

from flask import make_response

from remote_eink.api.display._common import (
    RemoteThreadImageStore,
    handle_display_controller_not_found_response,
    ImageTypeToMimeTypes,
)
from remote_eink.api.display.image import put_image


@handle_display_controller_not_found_response
def search(imageId: str, displayId: str):
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return image.metadata, HTTPStatus.OK


@handle_display_controller_not_found_response
def put(imageId: str, displayId: str, body: dict):
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Cannot put metadata as image does not exist: {imageId}", HTTPStatus.NOT_FOUND)
    return put_image(
        image_id=imageId,
        display_id=displayId,
        # XXX: the backwards-forward conversion of content type is perverse
        content_type=ImageTypeToMimeTypes[image.type][0],
        data=image.data,
        metadata=body,
        overwrite=True,
    )
