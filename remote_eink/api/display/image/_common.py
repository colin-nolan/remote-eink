from http import HTTPStatus
from typing import Callable, TypeVar, ParamSpec, Optional, Type

from marshmallow import Schema, fields

from remote_eink.api.display import to_target_process, display_id_handler
from remote_eink.api.display._common import CONTENT_TYPE_HEADER, ImageTypeToMimeType
from remote_eink.app_data import apps_data
from remote_eink.controllers.base import DisplayController
from remote_eink.images import FunctionBasedImage
from remote_eink.storage.image.base import ImageAlreadyExistsError

_T = TypeVar("_T")


class ImageMetadataSchema(Schema):
    rotation = fields.Float(data_key="rotation", default=0)


# def image_id_handler(to_wrap: Callable[..., _T]) -> Callable[..., _T]:
#     def wrapped(app_id: str, *args, **kwargs) -> _T:
#         app_data = apps_data[app_id]
#         kwargs["image_id"] = app_data.display_controllers
#         return to_wrap(*args, **kwargs)
#
#     return wrapped


@to_target_process
@display_id_handler
def put_image(
    display_controller: DisplayController,
    content_type: str,
    imageId: str,
    data: bytes,
    rotation: float = 0,
    *,
    overwrite: bool = True,
):
    if content_type is None:
        return f"{CONTENT_TYPE_HEADER} header is required", HTTPStatus.BAD_REQUEST

    image_type = ImageTypeToMimeType.inverse.get(content_type)
    if image_type is None:
        return (
            f"Unsupported image format: {image_type} (based on content type: {content_type})",
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    image = FunctionBasedImage(imageId, lambda: data, image_type, rotation=rotation)
    updated = False
    # FIXME: lock over both of these is required!
    if overwrite:
        updated = display_controller.image_store.remove(image.identifier)
    try:
        display_controller.image_store.add(image)
    except ImageAlreadyExistsError:
        return f"Image with same ID already exists: {imageId}", HTTPStatus.CONFLICT

    return imageId, HTTPStatus.CREATED if not updated else HTTPStatus.OK

