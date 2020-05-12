from http import HTTPStatus

from image_display_service.api.display._common import display_id_handler, ImageSchema
from image_display_service.display.controllers import DisplayController


@display_id_handler
def search(display_controller: DisplayController):
    images = display_controller.list_images()
    return ImageSchema(only=["identifier"]).dump(images, many=True), HTTPStatus.OK


@display_id_handler
def delete(display_controller: DisplayController):
    display_controller.clear()
    return "Image cleared", HTTPStatus.OK


@display_id_handler
def delete(display_controller: DisplayController):
    display_controller.clear()
    return "Image cleared", HTTPStatus.OK


@display_id_handler
def put(display_controller: DisplayController, imageId: str):
    display_controller.display(imageId)
    return f"Image displayed: {imageId}", HTTPStatus.OK
