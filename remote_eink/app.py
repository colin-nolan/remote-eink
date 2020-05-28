import os
from typing import Collection, Optional, Type
from uuid import uuid4

import connexion
from connexion import FlaskApp
from flask import Flask, current_app
from flask_cors import CORS

from remote_eink.app_storage import AppStorage, SynchronisedAppStorage
from remote_eink.display.controllers import DisplayController
from remote_eink.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

_apps = {}


def create_app(display_controllers: Collection[DisplayController],
               app_storage_class: Type[AppStorage] = SynchronisedAppStorage) -> Flask:
    """
    Creates the Flask app.
    :param display_controllers:
    :param app_storage_class:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("remote_eink.api"), strict_validation=True)
    CORS(app.app)

    app_identifier = str(uuid4())
    with app.app.app_context():
        app.app.config["identifier"] = app_identifier

    # Using external storage (opposed to Flask based) to guarantee process-safe synchronisation and locking
    global _apps
    _apps[app_identifier] = SynchronisedAppStorage.create() if app_storage_class is SynchronisedAppStorage \
        else app_storage_class()

    with get_app_storage(app=app.app).update_display_controllers() as existing_display_controllers:
        existing_display_controllers.clear()
        existing_display_controllers.update(
            {display_controller.identifier: display_controller for display_controller in display_controllers})

    return app


def destroy_app(app: Flask):
    """
    TODO
    :param app:
    :return:
    """
    with app.app_context():
        identifier = app.config["identifier"]
    del _apps[identifier]


def get_app_storage(app: Optional[Flask] = None) -> SynchronisedAppStorage:
    """
    TODO
    :param app:
    :return:
    """
    if app is None:
        app = current_app
    return _apps[app.config["identifier"]]
