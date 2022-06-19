from http import HTTPStatus

from remote_eink.api.display._common import (
    ImageSchema,
    RemoteThreadDisplayController,
    handle_display_controller_not_found_response,
)


@handle_display_controller_not_found_response
def search(displayId: str):
    display_controller = RemoteThreadDisplayController(displayId)
    if display_controller.current_image is None:
        return None, HTTPStatus.NOT_FOUND
    return ImageSchema(only=["identifier"]).dump(display_controller.current_image), HTTPStatus.OK


@handle_display_controller_not_found_response
def delete(displayId: str):
    display_controller = RemoteThreadDisplayController(displayId)
    display_controller.clear()
    return "Image cleared", HTTPStatus.OK


@handle_display_controller_not_found_response
def put(displayId: str, body: dict):
    if not isinstance(body, dict):
        return f"Body must be a map, got: {body}", HTTPStatus.BAD_REQUEST
    image_id = body.get("id")
    if image_id is None:
        return f'"id" field missing: {body}', HTTPStatus.BAD_REQUEST

    display_controller = RemoteThreadDisplayController(displayId)
    if display_controller.image_store.get(image_id) is None:
        return f"Image not found: {image_id}", HTTPStatus.BAD_REQUEST
    display_controller.display(image_id)
    return f"Image displayed: {image_id}", HTTPStatus.OK
