from typing import Tuple

from flask import current_app

from image_display_service.display.controllers import DisplayController

DISPLAY_CONTROLLERS_CONFIG_KEY = "DISPLAY_CONTROLLERS"


def get_display_controllers() -> Tuple[DisplayController]:
    """
    TODO
    :return:
    """
    return tuple(current_app.config[DISPLAY_CONTROLLERS_CONFIG_KEY])
