import os
from threading import Thread

from typing import Dict, Callable, Any, Iterable, Mapping

from remote_eink.controllers import DisplayController
from remote_eink.multiprocess import CommunicationPipe

apps_data: Dict[str, "AppData"] = {}


def _use_only_in_created_process(wrappable: Callable) -> Callable:
    """
    TODO
    :return:
    """

    def wrapped(self, *args, **kwargs) -> Any:
        if os.getpid() != self._created_pid:
            raise RuntimeError("Cannot access in process other than that which the app is created in")
        return wrappable(self, *args, **kwargs)

    return wrapped


class AppData:
    """
    TODO
    """

    @property
    def communication_pipe(self) -> CommunicationPipe:
        return self._communication_pipe

    @property
    @_use_only_in_created_process
    def display_controllers(self) -> Mapping[str, DisplayController]:
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
            raise ValueError(f'Display controller with ID "{display_controller.identifier}" already in collection')
        self._display_controllers[display_controller.identifier] = display_controller

    @_use_only_in_created_process
    def remove_display_controller(self, display_controller: DisplayController):
        """
        TODO
        """
        del self._display_controllers[display_controller.identifier]

    @_use_only_in_created_process
    def destroy(self):
        """
        TODO
        :return:
        """
        self.communication_pipe.sender.stop_receiver()
        self._communication_pipe = None
        self._display_controllers.clear()
