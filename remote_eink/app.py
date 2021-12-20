import os
from io import BytesIO

from uuid import uuid4

from typing import Collection, Optional

import connexion
from connexion import FlaskApp
from flask import Flask, current_app, Request
from flask_cors import CORS
from werkzeug.formparser import FormDataParser, MultiPartParser

from remote_eink.app_data import apps_data, AppData
from remote_eink.controllers import DisplayController
from remote_eink.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

APP_ID_PROPERTY = "APP_ID"


class MyMultiPartParser(MultiPartParser):
    def form_storage_builder(self, name, container, part_charset, headers):
        return b"".join(container).decode(part_charset, self.errors)


class MyFormDataParser(FormDataParser):
    multi_part_parser_class = MyMultiPartParser

    # def parse(self, stream, mimetype, content_length, options=None):
    #     if mimetype == "multipart/form-data":
    #         data = stream.read(content_length)
    #         print(data)
    #         result = super().parse(BytesIO(data), mimetype, content_length, options)
    #         print(result)
    #         return result
    #     else:
    #         return super().parse(stream, mimetype, content_length, options)


class MyRequest(Request):
    form_data_parser_class = MyFormDataParser


def create_app(display_controllers: Collection[DisplayController]) -> FlaskApp:
    """
    Creates the Flask app.
    :param display_controllers: display controllers that the created app should have
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    # Turning off strict validation due to bug: https://github.com/zalando/connexion/issues/1020#issuecomment-574437207
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("remote_eink.api"), strict_validation=False)
    CORS(app.app)

    identifier = str(uuid4())
    with app.app.app_context():
        app.app.config[APP_ID_PROPERTY] = identifier

    app.app.request_class = MyRequest

    apps_data[identifier] = AppData(display_controllers)

    return app.app


def get_app_data(app: Optional[Flask] = None) -> AppData:
    """
    Gets the app data for the given Flask app.
    :param app: Flask app to get data for (defaults to current app)
    :return: app data
    """
    app = app if app is not None else current_app
    with app.app_context():
        return apps_data[app.config[APP_ID_PROPERTY]]


def destroy_app(app: Optional[FlaskApp] = None):
    """
    Destroys the given flask app
    :param app: Flask app to destroy (defaults to current app)
    """
    app_data = get_app_data(app)
    app_data.destroy()
