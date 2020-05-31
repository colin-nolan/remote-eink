from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from multiprocessing import Lock, Event
from typing import Dict, ContextManager

from multiprocessing_on_dill.managers import SyncManager

from remote_eink.common import DisplayControllerNotFoundError
from remote_eink.controllers import DisplayController


class AppStorage(metaclass=ABCMeta):
    """
    TODO
    """
    @property
    @abstractmethod
    def display_controllers(self) -> Dict[str, DisplayController]:
        """
        TODO: warning that it's dangerous to update if read in progress
        :return:
        """

    @abstractmethod
    def update_display_controllers(self) -> ContextManager[Dict[str, DisplayController]]:
        """
        TODO
        :return:
        """

    @abstractmethod
    def update_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        """
        TODO
        :param identifier:
        :return:
        """

    @abstractmethod
    def use_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        """
        TODO
        :param identifier:
        :return:
        """


class NonSynchronisedAppStorage(AppStorage):
    """
    TODO
    """
    @property
    def display_controllers(self) -> Dict[str, DisplayController]:
        return dict(self._display_controllers)

    def __init__(self):
        self._display_controllers = {}

    @contextmanager
    def update_display_controllers(self) -> ContextManager[Dict[str, DisplayController]]:
        yield self._display_controllers

    @contextmanager
    def update_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        try:
            display_controller = self._display_controllers[identifier]
        except KeyError as e:
            raise DisplayControllerNotFoundError(identifier) from e
        yield display_controller
        self._display_controllers[display_controller] = display_controller

    @contextmanager
    def use_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        with self.update_display_controller(identifier) as display_controller:
            yield display_controller


class SynchronisedAppStorage(AppStorage):
    """
    TODO
    """
    @staticmethod
    def create():
        sync_manager = SyncManager()
        sync_manager.start()
        return SynchronisedAppStorage(sync_manager)

    @property
    def display_controllers(self) -> Dict[str, DisplayController]:
        return self._display_controllers

    @property
    def display_controller_user_count(self) -> int:
        return self._display_controllers_reader_counter

    @property
    def update_pending(self) -> bool:
        return not self._display_controllers_usage_allowed.is_set()

    def __init__(self, sync_manager: SyncManager):
        """
        TODO
        :param sync_manager:
        """
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

    @contextmanager
    def update_display_controllers(self) -> ContextManager[Dict[str, DisplayController]]:
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
        with self._use_display_controller(identifier, read_only=False) as display_controller:
            yield display_controller

    @contextmanager
    def use_display_controller(self, identifier: str) -> ContextManager[DisplayController]:
        with self._use_display_controller(identifier, read_only=True) as display_controller:
            yield display_controller

    @contextmanager
    def _use_display_controller(self, identifier: str, read_only: bool = False) -> ContextManager[DisplayController]:
        # Stop readers starving updater
        self._display_controllers_usage_allowed.wait()

        # Count reader in (so as to allow `update_display_controllers` to act only when no readers)
        with self._display_controllers_reader_counter_lock:
            self._display_controllers_reader_counter += 1
            self._display_controllers_reader_leave_event.clear()

        try:
            if identifier not in self._display_controllers:
                raise DisplayControllerNotFoundError(identifier)

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
