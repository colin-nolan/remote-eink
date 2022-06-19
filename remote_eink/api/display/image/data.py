from http import HTTPStatus
from io import BytesIO

from flask import make_response, send_file, request, Response

from remote_eink.api.display._common import (
    ImageTypeToMimeTypes,
    CONTENT_TYPE_HEADER,
    RemoteThreadImageStore,
)
from remote_eink.api.display.image import put_image
from remote_eink.api.display import handle_display_controller_not_found_response
from remote_eink.images import ImageType, DataBasedImage


@handle_display_controller_not_found_response
def search(imageId: str, displayId: str) -> Response:
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if image is None:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    return send_file(BytesIO(image.data), ImageTypeToMimeTypes[image.type][0])


def put(body: bytes, imageId: str, **kwargs) -> Response:
    # FIXME: implement
    # image = get_image(image_id=imageId, displayId=displayId)
    image = DataBasedImage("test", b"test", ImageType.JPG)
    # if image is None:
    #     return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    content_type = request.headers.get(CONTENT_TYPE_HEADER)
    return put_image(
        image_id=imageId,
        content_type=content_type,
        data=body,
        metadata=image.metadata,
        overwrite=True,
        **kwargs,
    )


# @to_target_process
# @display_id_handler
# def _get_data(display_controller: DisplayController, image_id: str) -> Optional[Tuple[BytesIO, str]]:
#     image = display_controller.image_store.get(image_id)
#
#     if image is None:
#         return None
#
#     return BytesIO(image.data), ImageTypeToMimeTypes[image.type][0]
