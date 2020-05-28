import os
from collections import defaultdict
from contextlib import contextmanager
from multiprocessing import Lock, Event
from typing import Collection, Set, ContextManager, Dict, Optional, Callable
from uuid import uuid4

import connexion
from connexion import FlaskApp
from flask import Flask, current_app
from flask_cors import CORS
from multiprocessing_on_dill.managers import SyncManager

from remote_eink.display.controllers import DisplayController
from remote_eink.resolver import CustomRestResolver

OPEN_API_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../openapi.yml")

_DISPLAY_CONTROLLERS_CONFIG_KEY = "DISPLAY_CONTROLLERS"

_sync_manager = SyncManager()
_sync_manager_lock = Lock()
_sync_manager_started = False


class InvalidDisplayControllerError(ValueError):
    """
    TODO
    """


class SynchronisedAppStorage:
    """
    TODO
    """
    @property
    def display_controller_user_count(self) -> int:
        return self._display_controllers_reader_counter

    @property
    def update_pending(self) -> bool:
        return not self._display_controllers_usage_allowed.is_set()

    def __init__(self, sync_manager: SyncManager = _sync_manager):
        self._display_controller_locks_update_lock = sync_manager.Lock()
        # What we really want to use is `multiprocessing.Value` but `SyncManager.Value` is not this:
        # https://bugs.python.org/issue35786
        self._display_controllers_reader_counter_lock: Lock = sync_manager.Lock()
        self._display_controllers_reader_counter = 0
        self._display_controllers_reader_leave_event: Event = sync_manager.Event()
        self._display_controllers_usage_allowed: Event = sync_manager.Event()
        self._display_controllers: Dict[str, DisplayController] = sync_manager.dict()
        self._display_controller_locks: Dict[str, Lock] = sync_manager.dict()
        self._create_lock: Lock = sync_manager.Lock

        # Set initial event values
        self._display_controllers_reader_leave_event.set()
        self._display_controllers_usage_allowed.set()

    def get_display_controller_ids(self) -> Set[str]:
        """
        TODO
        :return:
        """
        return set(self._display_controllers.keys())

    def get_display_controller(self, identifier: str) -> DisplayController:
        """
        TODO
        :param identifier:
        :return:
        """
        return self._display_controllers[identifier]

    def get_display_controllers(self) -> Set[DisplayController]:
        """
        TODO
        :return:
        """
        return set(self._display_controllers.values())

    @contextmanager
    def update_display_controllers(self) -> ContextManager[Dict[str, DisplayController]]:
        """
        TODO
        :return:
        """
        # Stop additional readers
        self._display_controllers_usage_allowed.clear()

        try:
            complete = False
            while not complete:
                self._display_controllers_reader_leave_event.wait()
                with self._display_controllers_reader_counter_lock:
                    if self._display_controllers_reader_counter == 0:
                        # Is this assignment-reassignment needed?
                        display_controllers = self._display_controllers
                        yield display_controllers
                        self._display_controllers = display_controllers
                        # No reads, no locks held. Clearing as may have entirely new set of display controllers now.
                        self._display_controller_locks.clear()
                        complete = True
        finally:
            # Allow readers again
            self._display_controllers_usage_allowed.set()

    @contextmanager
    def update_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        """
        TODO
        :param identifier:
        :return:
        """
        with self.update_display_controllers() as display_controllers:
            if identifier not in display_controllers:
                raise InvalidDisplayControllerError(identifier)
            # Must be assigned and reassigned to force sync update
            display_controller = display_controllers[identifier]
            yield display_controller
            display_controllers[identifier] = display_controller

    @contextmanager
    def use_display_controller(self, identifier: str, *, read_only: bool = False) -> ContextManager[DisplayController]:
        """
        TODO
        :param identifier:
        :param read_only:
        :return:
        """
        # Stop readers starving updater
        self._display_controllers_usage_allowed.wait()

        # Count reader in (so as to allow `update_display_controllers` to act only when no readers)
        with self._display_controllers_reader_counter_lock:
            self._display_controllers_reader_counter += 1
            self._display_controllers_reader_leave_event.clear()

        try:
            if identifier not in self._display_controllers:
                raise InvalidDisplayControllerError(identifier)

            if not read_only:
                # The existence of the lock is checked and assigned under a global lock to ensure that everyone is
                # referring to the same lock. The check is lightweight so shouldn't block for too long. However, there
                # are likely more complicated ways of doing this without a global lock.
                with self._display_controller_locks_update_lock:
                    if identifier not in self._display_controller_locks:
                        self._display_controller_locks[identifier] = self._create_lock()

                with self._display_controller_locks[identifier]:
                    # Must be assigned due to reassign below
                    display_controller = self._display_controllers[identifier]
                    yield display_controller
                    # Re-assign to notify the proxy of the update
                    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing-proxy-objects
                    self._display_controllers[identifier] = display_controller
            else:
                # There is no guarantee that the read is exactly up to date
                yield self._display_controllers[identifier]

        finally:
            # Count reader out
            with self._display_controllers_reader_counter_lock:
                self._display_controllers_reader_counter -= 1
            self._display_controllers_reader_leave_event.set()


_apps = defaultdict(SynchronisedAppStorage)


def create_app(display_controllers: Collection[DisplayController]) -> FlaskApp:
    """
    Creates the Flask app.
    :param display_controllers:
    :return: Flask app
    """
    app = connexion.App(__name__, options=dict(swagger_ui=True))
    app.add_api(OPEN_API_LOCATION, resolver=CustomRestResolver("remote_eink.api"), strict_validation=True)
    CORS(app.app)

    app_identifier = str(uuid4())
    with app.app.app_context():
        app.app.config["identifier"] = app_identifier

    with _sync_manager_lock:
        global _sync_manager_started, _sync_manager
        if not _sync_manager_started:
            _sync_manager.start()
            _sync_manager_started = True

    with get_synchronised_app_storage(app=app.app).update_display_controllers() as existing_display_controllers:
        existing_display_controllers.clear()
        existing_display_controllers.update(
            {display_controller.identifier: display_controller for display_controller in display_controllers})

    return app


def get_synchronised_app_storage(app: Optional[Flask] = None) -> SynchronisedAppStorage:
    """
    TODO
    :param app:
    :return:
    """
    if app is None:
        app = current_app
    return _apps[app.config["identifier"]]
