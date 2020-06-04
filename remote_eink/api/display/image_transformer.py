from enum import unique, Enum
from http import HTTPStatus

from typing import Dict, Callable

from marshmallow import Schema, fields

from remote_eink.api.display._common import display_id_handler
from remote_eink.controllers import DisplayController
from remote_eink.transformers import ImageTransformer
from remote_eink.transformers.base import InvalidConfigurationError, InvalidPositionError


@unique
class ModifiableParameter(Enum):
    """
    TODO
    """
    POSITION = "position"
    CONFIGURATION = "configuration"


class _ImageTransformerSchema(Schema):
    identifier = fields.Str(data_key="id")
    description = fields.Str(data_key="description")
    active = fields.Bool(data_key="active")
    configuration = fields.Dict(data_key="configuration")


def image_transformer_id_handler(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable: handler to wrap
    :return: TODO
    """
    def wrapped(display_controller: DisplayController, imageTransformerId: str, **kwargs):
        image_transformer = display_controller.image_transformers.get_by_id(imageTransformerId)
        if image_transformer is None:
            return f"No matching image transformer with ID: {imageTransformerId}", HTTPStatus.NOT_FOUND
        return wrappable(display_controller=display_controller, image_transformer=image_transformer, **kwargs)

    return wrapped


def image_transformer_position_handler(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable: handler to wrap
    :return: TODO
    """
    def wrapped(display_controller: DisplayController, image_transformer: ImageTransformer, **kwargs):
        position = display_controller.image_transformers.get_position(image_transformer)
        return wrappable(
            display_controller=display_controller, image_transformer=image_transformer, position=position, **kwargs)

    return wrapped


@display_id_handler
def search(display_controller: DisplayController):
    image_transformers = display_controller.image_transformers
    return _ImageTransformerSchema(only=["identifier"]).dump(image_transformers, many=True), HTTPStatus.OK


@display_id_handler
@image_transformer_id_handler
@image_transformer_position_handler
def get(display_controller: DisplayController, image_transformer: ImageTransformer, position: int):
    # XXX: there is probably a better way to deal with the concept of "position"
    serialised_image_transformer = dict(**_ImageTransformerSchema().dump(image_transformer), position=position)
    return serialised_image_transformer, HTTPStatus.OK


@display_id_handler
@image_transformer_id_handler
@image_transformer_position_handler
def put(display_controller: DisplayController, image_transformer: ImageTransformer, position: int, body: Dict):
    unsupported_parameters = set(body.keys()) - set(x.value for x in ModifiableParameter)
    if len(unsupported_parameters) > 0:
        return f"Cannot set parameters: {unsupported_parameters}. ", HTTPStatus.BAD_REQUEST

    configuration = body.get(ModifiableParameter.CONFIGURATION.value)
    if configuration is not None:
        try:
            image_transformer.modify_configuration(configuration)
        except InvalidConfigurationError as e:
            return str(e), HTTPStatus.BAD_REQUEST

    modified_position = body.get(ModifiableParameter.POSITION.value)
    if modified_position is not None:
        if not isinstance(modified_position, int):
            return f"Position must be integer: {modified_position}", HTTPStatus.BAD_REQUEST
        modified_position = int(modified_position)
        if modified_position != position:
            try:
                display_controller.image_transformers.set_position(image_transformer, modified_position)
            except InvalidPositionError:
                return f"Invalid position: {modified_position}", HTTPStatus.BAD_REQUEST

    return "Configuration updated", HTTPStatus.OK
