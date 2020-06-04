import inspect
import os
from threading import Thread
from typing import Collection, Optional, Dict, Callable

import connexion
from flask import Flask, current_app
from flask_cors import CORS

from remote_eink.controllers import DisplayController
from remote_eink.multiprocess import MultiprocessDisplayController, MultiprocessDisplayControllerReceiver
from remote_eink.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

DISPLAY_CONTROLLER_RECEIVER_PROPERTY = "DISPLAY_CONTROLLER_RECEIVER"
CREATED_PID_PROPERTY = "CREATED_PID"

_apps = {}


def create_app(display_controllers: Collection[DisplayController]) -> Flask:
    """
    Creates the Flask app.
    :param display_controllers:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("remote_eink.api"), strict_validation=True)
    CORS(app.app)

    with app.app.app_context():
        app.app.config[CREATED_PID_PROPERTY] = os.getpid()
        app.app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY] = {}
        for display_controller in display_controllers:
            add_display_controller(display_controller, app.app)

    return app.app


def _app_from_context_if_none(wrappable: Callable) -> Callable:
    arg_spec = inspect.getfullargspec(wrappable).args
    app_parameter = "app"

    def wrapper(*args, **kwargs):
        nonlocal arg_spec
        if app_parameter in kwargs:
            if kwargs[app_parameter] is None:
                kwargs[app_parameter] = current_app
        else:
            try:
                positional_arg_index = arg_spec.index(app_parameter)
            except ValueError:
                raise AssertionError(f"Annotation must be used on method with the parameter: {app_parameter}")
            args = list(args)
            if positional_arg_index == len(args):
                args.append(current_app)
            elif positional_arg_index > len(args):
                # Can only assume it's not a positional only argument
                kwargs[app_parameter] = current_app
            args = tuple(args)

        return wrappable(*args, **kwargs)

    return wrapper


def _ensure_execute_in_created_process(app: Flask):
    """
    TODO
    :param app:
    :return:
    :raises NotImplementedError:
    """
    with app.app_context():
        if os.getpid() != app.config[CREATED_PID_PROPERTY]:
            raise NotImplementedError(
                "Only adding display controllers in process where the app is created is currently supported")



# TODO: app None annotation
@_app_from_context_if_none
def destroy_app(app: Flask):
    """
    TODO
    :param app:
    :return:
    """
    _ensure_execute_in_created_process(app)

    with app.app_context():
        for display_controller_id, display_controller_receiver in app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY].copy().items():
            display_controller_receiver.connector.send(MultiprocessDisplayControllerReceiver.RUN_POISON)
            del app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY][display_controller_id]


@_app_from_context_if_none
def add_display_controller(display_controller: DisplayController, app: Optional[Flask] = None):
    """
    TODO
    :param app:
    :return:
    """
    _ensure_execute_in_created_process(app)

    with app.app_context():
        # TODO: tidy up
        display_controller_receiver = MultiprocessDisplayControllerReceiver(display_controller)
        Thread(target=display_controller_receiver.run).start()
        assert display_controller.identifier not in current_app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY]
        current_app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY][display_controller.identifier] = \
            display_controller_receiver


@_app_from_context_if_none
def get_display_controllers(app: Optional[Flask] = None) -> Dict[str, DisplayController]:
    """
    TODO
    :param app:
    :return:
    """
    with app.app_context():
        return {identifier: MultiprocessDisplayController(receiver.connector)
                for identifier, receiver in current_app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY].items()}


@_app_from_context_if_none
def get_display_controller(display_controller_id: str, app: Optional[Flask] = None) -> DisplayController:
    """
    TODO
    :param display_controller_id:
    :param app:
    :return:
    """
    with app.app_context():
        receiver = current_app.config[DISPLAY_CONTROLLER_RECEIVER_PROPERTY][display_controller_id]
        return MultiprocessDisplayController(receiver.connector)
