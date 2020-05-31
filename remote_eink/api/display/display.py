from http import HTTPStatus

from remote_eink.api.display._common import display_id_handler, ImageSchema
from remote_eink.app import get_app_storage
from remote_eink.controllers import DisplayController
from marshmallow import Schema, fields


class _DisplayControllerSchema(Schema):
    identifier = fields.Str(data_key="id")
    current_image = fields.Nested(ImageSchema, only=["identifier"], data_key="currentImage")
    images = fields.Function(lambda display_controller: ImageSchema(only=["identifier"]).dump(
        display_controller.image_store.list(), many=True))
    image_orientation = fields.Integer(data_key="orientation")
    cycle_images = fields.Bool(data_key="cycleImages")
    cycle_images_randomly = fields.Bool(data_key="cycleRandomly")
    cycle_image_after_seconds = fields.Integer(data_key="cycleAfterSeconds")


def search():
    return [{"id": identifier} for identifier in get_app_storage().display_controllers.keys()], \
           HTTPStatus.OK


@display_id_handler
def get(display_controller: DisplayController):
    return _DisplayControllerSchema().dump(display_controller), HTTPStatus.OK
