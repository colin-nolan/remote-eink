from enum import unique, Enum
from http import HTTPStatus
from typing import Dict

from flask import Response, make_response
from marshmallow import Schema, fields

from remote_eink.api.display._common import (
    RemoteThreadImageTransformerSequence,
    handle_display_controller_not_found_response,
)
from remote_eink.transformers.base import InvalidConfigurationError, InvalidPositionError


@handle_display_controller_not_found_response
def search(displayId: str):
    image_transformers = RemoteThreadImageTransformerSequence(displayId)
    return _ImageTransformerSchema(only=["identifier"]).dump(image_transformers, many=True), HTTPStatus.OK


@handle_display_controller_not_found_response
def get(displayId: str, imageTransformerId: str) -> Response:
    image_transformers = RemoteThreadImageTransformerSequence(displayId)
    try:
        # Both should be in try block as it's possible for it to be removed mid-operation due to the lack of lock
        image_transformer = image_transformers.get_by_id(imageTransformerId)
        position = image_transformers.get_position(imageTransformerId)
    except KeyError:
        return make_response(
            f"Image transformer with given ID does not exist: {imageTransformerId}", HTTPStatus.NOT_FOUND
        )

    # XXX: there is probably a better way to deal with the concept of "position"
    serialised_image_transformer = dict(**_ImageTransformerSchema().dump(image_transformer), position=position)
    return make_response(serialised_image_transformer, HTTPStatus.OK)


@handle_display_controller_not_found_response
def put(displayId: str, imageTransformerId: str, body: Dict) -> Response:
    image_transformers = RemoteThreadImageTransformerSequence(displayId)
    try:
        # Both should be in try block as it's possible for it to be removed mid-operation due to the lack of lock
        image_transformer = image_transformers.get_by_id(imageTransformerId)
        position = image_transformers.get_position(imageTransformerId)
    except KeyError:
        return make_response(
            f"Image transformer with given ID does not exist: {imageTransformerId}", HTTPStatus.NOT_FOUND
        )

    unsupported_parameters = set(body.keys()) - set(x.value for x in _ModifiableParameter)
    if len(unsupported_parameters) > 0:
        return make_response(f"Cannot set parameters: {unsupported_parameters}. ", HTTPStatus.BAD_REQUEST)

    configuration = body.get(_ModifiableParameter.CONFIGURATION.value)
    if configuration is not None:
        try:
            image_transformer.modify_configuration(configuration)
        except InvalidConfigurationError as e:
            return make_response(str(e), HTTPStatus.BAD_REQUEST)

    modified_position = body.get(_ModifiableParameter.POSITION.value)
    if modified_position is not None:
        if not isinstance(modified_position, int):
            return make_response(f"Position must be integer: {modified_position}", HTTPStatus.BAD_REQUEST)
        modified_position = int(modified_position)
        if modified_position != position:
            try:
                image_transformers.set_position(image_transformer.identifier, modified_position)
            except InvalidPositionError:
                return make_response(f"Invalid position: {modified_position}", HTTPStatus.BAD_REQUEST)

    return make_response("Configuration updated", HTTPStatus.OK)


# TODO: support for deleting transformer?


@unique
class _ModifiableParameter(Enum):
    POSITION = "position"
    CONFIGURATION = "configuration"


class _ImageTransformerSchema(Schema):
    identifier = fields.Str(data_key="id")
    description = fields.Str(data_key="description")
    active = fields.Bool(data_key="active")
    configuration = fields.Dict(data_key="configuration")
