import json

from image_display_service.common import get_display_controllers
from marshmallow import Schema, fields


class DisplayControllerSchema(Schema):
    identifier = fields.Str(data_key="id")
    current_image = fields.Function(lambda obj: obj.current_image.identifier if obj.current_image else None,
                                    data_key="currentImage")
    images = fields.Function(lambda obj: [image.identifier for image in obj.images], data_key="images")
    image_orientation = fields.Integer(data_key="orientation")
    cycle_images = fields.Bool(data_key="cycleImages")
    cycle_images_randomly = fields.Bool(data_key="cycleRandomly")
    cycle_image_after_seconds = fields.Integer(data_key="cycleAfterSeconds")


display_controller_schema = DisplayControllerSchema()


def search():
    identifiers = list(get_display_controllers().keys())
    return json.dumps(identifiers), 200


def get(displayId: str):
    display_controller = get_display_controllers().get(displayId)
    if display_controller is None:
        return f"Display not found: {displayId}", 404
    return display_controller_schema.dumps(display_controller)
