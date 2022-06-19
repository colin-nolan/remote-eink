import io
import json
from http import HTTPStatus
from types import MappingProxyType

from PIL import Image as PilImage
from PIL import UnidentifiedImageError
from flask import make_response, Response
from marshmallow import Schema, fields

from remote_eink.api.display._common import (
    CONTENT_TYPE_HEADER,
    MimeTypeToImageType,
    to_target_process,
    _display_id_handler,
    handle_display_controller_not_found_response,
)
from remote_eink.controllers.base import DisplayController
from remote_eink.images import FunctionBasedImage, Image
from remote_eink.storage.image.base import ImageAlreadyExistsError


@handle_display_controller_not_found_response
def put_image(
    image_id: str,
    display_id: str,
    content_type: str,
    data: bytes,
    metadata: dict = MappingProxyType({}),
    *,
    overwrite: bool,
) -> Response:
    if content_type is None:
        return make_response(f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST)

    image_type = MimeTypeToImageType.get(content_type)
    if image_type is None:
        # TODO: try sniffing
        return make_response(
            f"Unsupported image format: {image_type} (based on content type: {content_type})",
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    try:
        PilImage.open(io.BytesIO(data))
    except UnidentifiedImageError:
        return make_response("Invalid image file data", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    # TODO: full metadata support
    image = FunctionBasedImage(image_id, lambda: data, image_type, metadata=metadata)

    try:
        updated = _put_image(image=image, overwrite=overwrite, displayId=display_id)
    except ImageAlreadyExistsError:
        return make_response(f"Image with same ID already exists: {image_id}", HTTPStatus.CONFLICT)

    return Response(
        response=json.dumps({"id": image_id}),
        status=HTTPStatus.CREATED if not updated else HTTPStatus.OK,
        mimetype="application/json",
    )


# FIXME
@to_target_process
@_display_id_handler
def _put_image(display_controller: DisplayController, image: Image, overwrite: bool) -> bool:
    # FIXME: lock required!
    if not overwrite and display_controller.image_store.get(image.identifier) is not None:
        raise ImageAlreadyExistsError(image.identifier)
    updated = display_controller.image_store.remove(image.identifier)
    display_controller.image_store.add(image)
    return updated
