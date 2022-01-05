from http import HTTPStatus
from typing import Dict

from remote_eink.api.display._common import display_id_handler, ImageSchema, to_target_process
from remote_eink.controllers.base import DisplayController


@to_target_process
@display_id_handler
def search(display_controller: DisplayController):
    if display_controller.current_image is None:
        return None, HTTPStatus.NOT_FOUND
    return ImageSchema(only=["identifier"]).dump(display_controller.current_image), HTTPStatus.OK


@to_target_process
@display_id_handler
def delete(display_controller: DisplayController):
    display_controller.clear()
    return "Image cleared", HTTPStatus.OK


@to_target_process
@display_id_handler
def put(display_controller: DisplayController, body: Dict):
    if not isinstance(body, Dict):
        return f"Body must be a map, got: {body}", HTTPStatus.BAD_REQUEST
    image_id = body.get("id")
    if image_id is None:
        return f'"id" field missing: {body}', HTTPStatus.BAD_REQUEST
    if display_controller.image_store.get(image_id) is None:
        return f"Image not found: {image_id}", HTTPStatus.BAD_REQUEST
    display_controller.display(image_id)
    return f"Image displayed: {image_id}", HTTPStatus.OK
