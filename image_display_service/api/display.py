import json

from image_display_service.common import get_display_controllers


def search():
    ids = [display_controller.identifier for display_controller in get_display_controllers()]
    return json.dumps(ids), 200


def get(displayId: str):
    pass
