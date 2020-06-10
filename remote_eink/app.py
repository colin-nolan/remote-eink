import inspect
import os
from uuid import uuid4

from threading import Thread
from typing import Collection, Dict, Callable, Iterable, Any

import connexion
from flask import Flask, current_app
from flask_cors import CORS

from remote_eink.controllers import DisplayController
from remote_eink.multiprocess import CommunicationPipe
from remote_eink.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

APP_ID_PROPERTY = "APP_ID"

apps_data: Dict[str, "AppData"] = {}


def _use_only_in_created_process(wrappable: Callable) -> Callable:
    """
    TODO
    :return:
    """
    def wrapped(self, *args, **kwargs) -> Any:
        if os.getpid() != self._created_pid:
            raise RuntimeError("Cannot access in process other than that which the app is created in")

    return wrappable


class AppData:
    """
    TODO
    """
    @property
    def communication_pipe(self) -> CommunicationPipe:
        return self._communication_pipe

    @property
    @_use_only_in_created_process
    def display_controllers(self) -> Dict[str, DisplayController]:
        return dict(self._display_controllers)

    def __init__(self, display_controllers: Iterable[DisplayController]):
        """
        Constructor.
        :param display_controllers: TODO
        """
        self._display_controllers: Dict[str, DisplayController] = {}

        communication_pipe = CommunicationPipe()
        Thread(target=communication_pipe.receiver.run).start()
        self._communication_pipe = communication_pipe
        self._created_pid = os.getpid()

        for display_controller in display_controllers:
            self.add_display_controller(display_controller)

    @_use_only_in_created_process
    def add_display_controller(self, display_controller: DisplayController):
        """
        TODO
        """
        if display_controller.identifier in self._display_controllers:
            raise ValueError(f"Display controller with ID \"{display_controller.identifier}\" already in collection")
        self._display_controllers[display_controller.identifier] = display_controller

    @_use_only_in_created_process
    def destroy(self):
        """
        TODO
        :return:
        """
        self.communication_pipe.sender.stop_receiver()
        self._communication_pipe = None
        self._display_controllers.clear()


def create_app(display_controllers: Collection[DisplayController]) -> Flask:
    """
    Creates the Flask app.
    :param display_controllers:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("remote_eink.api"), strict_validation=True)
    CORS(app.app)

    identifier = str(uuid4())
    with app.app.app_context():
        app.app.config[APP_ID_PROPERTY] = identifier

    apps_data[identifier] = AppData(display_controllers)

    return app.app


# TODO: to app_data
def _app_from_context_if_none(wrappable: Callable) -> Callable:
    """
    TODO
    :param wrappable:
    :return:
    """
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


@_app_from_context_if_none
def add_display_controller(display_controller: DisplayController, app: Flask):
    """
    TODO
    :param display_controller:
    :param app:
    :return:
    """
    with app.app_context():
        app_data: AppData = apps_data[app.config[APP_ID_PROPERTY]]
    app_data.add_display_controller(display_controller)


@_app_from_context_if_none
def destroy_app(app: Flask):
    """
    TODO
    :param app:
    :return:
    """
    with app.app_context():
        app_data: AppData = apps_data[app.config[APP_ID_PROPERTY]]

    app_data.destroy()
    # TODO: anything else required to stop Flask?


# TODO
# def _ensure_execute_in_created_process(app: AppData):
#     """
#     TODO
#     :param app:
#     :return:
#     :raises NotImplementedError:
#     """
#     with app.app_context():
#         if os.getpid() != app.config[CREATED_PID_PROPERTY]:
#             raise NotImplementedError(
#                 "Only adding display controllers in process where the app is created is currently supported")
