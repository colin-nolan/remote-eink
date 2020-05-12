import os
from typing import Collection, Dict

import connexion
from connexion import FlaskApp
from flask import current_app
from flask_cors import CORS

from image_display_service.display.controllers import DisplayController
from image_display_service.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

DISPLAY_CONTROLLERS_CONFIG_KEY = "DISPLAY_CONTROLLERS"


def get_display_controllers() -> Dict[str, DisplayController]:
    """
    Gets the display controllers configured on the app.
    :return: display controllers, mapped by the controllers identifiers
    """
    return {controller.identifier: controller for controller in current_app.config[DISPLAY_CONTROLLERS_CONFIG_KEY]}


def create_app(display_controllers: Collection[DisplayController]) -> FlaskApp:
    """
    Creates the Flask app.
    :param display_controllers:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("image_display_service.api"), strict_validation=True)
    CORS(app.app)

    with app.app.app_context():
        app.app.config[DISPLAY_CONTROLLERS_CONFIG_KEY] = display_controllers

    return app
