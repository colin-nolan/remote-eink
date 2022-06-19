from http import HTTPStatus
from io import BytesIO

from flask import make_response, send_file, request, Response

from remote_eink.api.display import handle_display_controller_not_found_response
from remote_eink.api.display._common import (
    ImageTypeToMimeTypes,
    CONTENT_TYPE_HEADER,
    RemoteThreadImageStore,
)
from remote_eink.api.display.image import put_image


@handle_display_controller_not_found_response
def search(imageId: str, displayId: str) -> Response:
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    return send_file(BytesIO(image.data), ImageTypeToMimeTypes[image.type][0])


@handle_display_controller_not_found_response
def put(imageId: str, displayId: str, body: bytes) -> Response:
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    content_type = request.headers.get(CONTENT_TYPE_HEADER)
    return put_image(
        image_id=imageId,
        display_id=displayId,
        content_type=content_type,
        data=body,
        metadata=image.metadata,
        overwrite=True,
    )
