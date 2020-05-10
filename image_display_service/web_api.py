import os
from typing import Collection, Dict

import connexion
from connexion import FlaskApp, RestyResolver
from flask import current_app
from flask_cors import CORS

from image_display_service.display.controllers import DisplayController
from image_display_service.resolver import ExtendedRestyResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")


def create_app(display_controllers: Collection[DisplayController]) -> FlaskApp:
    """
    Creates the Flask app.
    :param display_controllers:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=ExtendedRestyResolver("image_display_service.api"), strict_validation=True)
    CORS(app.app)

    with app.app.app_context():
        app.app.config[DISPLAY_CONTROLLERS_CONFIG_KEY] = display_controllers

    return app


DISPLAY_CONTROLLERS_CONFIG_KEY = "DISPLAY_CONTROLLERS"


def get_display_controllers() -> Dict[str, DisplayController]:
    """
    TODO
    :return:
    """
    return {controller.identifier: controller for controller in current_app.config[DISPLAY_CONTROLLERS_CONFIG_KEY]}