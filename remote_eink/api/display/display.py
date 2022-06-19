from http import HTTPStatus
from typing import Iterable

from marshmallow import Schema, fields

from remote_eink.api.display._common import (
    ImageSchema,
    to_target_process,
    RemoteThreadDisplayController,
    handle_display_controller_not_found_response,
)
from remote_eink.app_data import apps_data


def search():
    return [{"id": identifier} for identifier in _get_display_controller_ids()], HTTPStatus.OK


@handle_display_controller_not_found_response
def get(displayId: str):
    display_controller = RemoteThreadDisplayController(displayId)
    return _DisplayControllerSchema().dump(display_controller), HTTPStatus.OK


@to_target_process
def _get_display_controller_ids(app_id: str) -> Iterable[str]:
    """
    Gets iterable of controller IDs.
    :param app_id: injected from `to_target_process`
    :return: iterable of IDs
    """
    app_data = apps_data[app_id]
    return tuple(app_data.display_controllers.keys())


class _DisplayControllerSchema(Schema):
    identifier = fields.Str(data_key="id")
    display_controller_type = fields.Function(
        lambda display_controller: display_controller.friendly_type_name, data_key="type"
    )
    image_storage_type = fields.Function(
        lambda display_controller: display_controller.image_store.friendly_type_name, data_key="storageType"
    )
    current_image = fields.Nested(ImageSchema, only=["identifier"], data_key="currentImage")
    images = fields.Function(
        lambda display_controller: ImageSchema(only=["identifier"]).dump(
            display_controller.image_store.list(), many=True
        )
    )
    image_orientation = fields.Integer(data_key="orientation")
    cycle_images = fields.Bool(data_key="cycleImages")
    cycle_images_randomly = fields.Bool(data_key="cycleRandomly")
    cycle_image_after_seconds = fields.Integer(data_key="cycleAfterSeconds")
