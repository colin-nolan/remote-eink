import json
from http import HTTPStatus
from io import BytesIO
from uuid import uuid4

from flask import request, Response, make_response
from requests_toolbelt import MultipartEncoder

from remote_eink.api.display._common import (
    CONTENT_TYPE_HEADER,
    ImageSchema,
    ImageTypeToMimeTypes,
    RemoteThreadImageStore,
    handle_display_controller_not_found_response,
)
from remote_eink.api.display.image._common import (
    put_image,
)


@handle_display_controller_not_found_response
def search(displayId: str):
    images = RemoteThreadImageStore(displayId).list()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


@handle_display_controller_not_found_response
def get(imageId: str, displayId: str) -> Response:
    image = RemoteThreadImageStore(displayId).get(image_id=imageId)
    if not image:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)

    multipart_content = MultipartEncoder(
        fields={
            "metadata": (None, json.dumps(image.metadata), "application/json"),
            "data": (None, BytesIO(image.data), ImageTypeToMimeTypes[image.type][0]),
        }
    )

    return Response(multipart_content.to_string(), mimetype=multipart_content.content_type)


def put(imageId: str, **kwargs) -> Response:
    content_type = request.headers.get(CONTENT_TYPE_HEADER)

    if content_type is None or not content_type.startswith("multipart/form-data"):
        return make_response(
            f"Unsupported content type (expected 'multipart/form-data'): {CONTENT_TYPE_HEADER}",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        data = kwargs["data"]
    except KeyError:
        return make_response(
            f"No data supplied",
            HTTPStatus.BAD_REQUEST,
        )

    content_type = kwargs["data"].content_type
    metadata = kwargs["body"]["metadata"]
    data = data.stream.read()

    del kwargs["body"]
    del kwargs["data"]

    if "overwrite" not in kwargs:
        kwargs["overwrite"] = True

    return put_image(image_id=imageId, content_type=content_type, data=data, metadata=metadata, **kwargs)


def post(**kwargs) -> Response:
    return put(str(uuid4()), **kwargs, overwrite=False)


@handle_display_controller_not_found_response
def delete(imageId: str, displayId: str) -> Response:
    deleted = RemoteThreadImageStore(displayId).remove(image_id=imageId)
    if not deleted:
        return make_response(f"Image not found: {imageId}", HTTPStatus.NOT_FOUND)
    return make_response(f"Deleted: {imageId}", HTTPStatus.OK)
