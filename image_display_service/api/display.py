import json
from typing import Tuple, Union

from image_display_service.display.controllers import DisplayController
from image_display_service.web_api import get_display_controllers
from marshmallow import Schema, fields


class ImageSchema(Schema):
    identifier = fields.Str(data_key="id")


class DisplayControllerSchema(Schema):
    identifier = fields.Str(data_key="id")
    current_image = fields.Nested(ImageSchema, only=["identifier"], data_key="currentImage")
    images = fields.Function(lambda display_controller: ImageSchema(only=["identifier"]).dump(
        display_controller.image_store.list(), many=True))
    image_orientation = fields.Integer(data_key="orientation")
    cycle_images = fields.Bool(data_key="cycleImages")
    cycle_images_randomly = fields.Bool(data_key="cycleRandomly")
    cycle_image_after_seconds = fields.Integer(data_key="cycleAfterSeconds")


def search() -> Tuple[str, int]:
    identifiers = list(get_display_controllers().keys())
    return json.dumps(identifiers), 200


def get(displayId: str) -> Tuple[str, int]:
    display_controller = get_display_controllers().get(displayId)
    if display_controller is None:
        return f"Display not found: {displayId}", 404
    return DisplayControllerSchema().dumps(display_controller), 200


def image_search(displayId: str) -> Tuple[str, int]:
    display_controller = get_display_controllers().get(displayId)

    if display_controller is None:
        return f"Display not found: {displayId}", 404

    images = display_controller.image_store.list()
    return ImageSchema(only=["identifier"]).dumps(images, many=True), 200


def image_get(displayId: str, imageId: str) -> Tuple[Union[bytes, str], int]:
    display_controller = get_display_controllers().get(displayId)
    image = display_controller.image_store.retrieve(imageId)

    if image is None:
        return f"Image not found: {imageId}", 404

    return image.data, 200

