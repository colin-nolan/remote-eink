from typing import Dict

from flask import current_app

from image_display_service.display.controllers import DisplayController

DISPLAY_CONTROLLERS_CONFIG_KEY = "DISPLAY_CONTROLLERS"


def get_display_controllers() -> Dict[str, DisplayController]:
    """
    TODO
    :return:
    """
    return {controller.identifier: controller for controller in current_app.config[DISPLAY_CONTROLLERS_CONFIG_KEY]}
