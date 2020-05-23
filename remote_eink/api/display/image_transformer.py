from http import HTTPStatus

from marshmallow import Schema, fields

from remote_eink.api.display._common import display_id_handler
from remote_eink.display.controllers import DisplayController


class _ImageTransformerSchema(Schema):
    identifier = fields.Str(data_key="id")
    description = fields.Str(data_key="description")
    active = fields.Bool(data_key="active")
    configuration = fields.Dict(data_key="configuration")


@display_id_handler
def search(display_controller: DisplayController):
    image_transformers = display_controller.image_transformers
    return _ImageTransformerSchema(only=["identifier"]).dump(image_transformers, many=True), HTTPStatus.OK


@display_id_handler
def get(display_controller: DisplayController, imageTransformerId: str):
    image_transformer, position = display_controller.image_transformers.get_by_id(imageTransformerId)
    if image_transformer is None:
        return f"No matching image transformer with ID: {imageTransformerId}", HTTPStatus.NOT_FOUND

    serialised_image_transformer = dict(**_ImageTransformerSchema().dump(image_transformer), position=position)
    return serialised_image_transformer, HTTPStatus.OK
