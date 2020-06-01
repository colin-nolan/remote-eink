from multiprocessing.connection import Connection, Pipe
from typing import Any, Optional

from remote_eink.controllers import DisplayController
from remote_eink.drivers.base import DisplayDriver
from remote_eink.models import Image
from remote_eink.storage.images import ImageStore
from remote_eink.transformers import ImageTransformerSequence


class MultiprocessDisplayDriver(DisplayDriver):
    """
    TODO
    """
    @property
    def sleeping(self) -> bool:
        self._connection.send(("display_driver.sleeping", [], {}))
        return self._connection.recv()

    @property
    def image(self) -> Optional[Image]:
        self._connection.send(("display_driver.image", [], {}))
        return self._connection.recv()

    def __init__(self, connection: Connection):
        self._connection = connection

    def display(self, image_data: bytes):
        self._connection.send(("display_driver.display", [image_data], {}))

    def clear(self):
        self._connection.send(("display_driver.clear", [], {}))

    def sleep(self):
        self._connection.send(("display_driver.sleep", [], {}))

    def wake(self):
        self._connection.send(("display_driver.wake", [], {}))


class MultiprocessDisplayController(DisplayController):
    """
    TODO
    """
    @property
    def current_image(self) -> Image:
        self._connection.send(("current_image", [], {}))
        return self._connection.recv()

    @property
    def driver(self) -> DisplayDriver:
        return MultiprocessDisplayDriver(self._connection)

    @property
    def image_store(self) -> ImageStore:
        pass

    @property
    def image_transformers(self) -> ImageTransformerSequence:
        pass

    def __init__(self, connection: Connection):
        self._connection = connection

    def display(self, image_id: str):
        self._connection.send(("display", [image_id], {}))

    def clear(self):
        self._connection.send(("clear", [], {}))

    def apply_image_transforms(self, image: Image) -> Image:
        pass


class MultiprocessDisplayControllerReceiver:
    """
    TODO
    """
    @property
    def connector(self) -> Connection:
        if not self._started:
            raise RuntimeError("Controller not started")
        return self._child_connection

    def __init__(self, display_controller: DisplayController):
        self._display_controller = display_controller
        self._parent_connection, self._child_connection = Pipe(duplex=False)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("Already started")
        while self._started:
            try:
                method_name, args, kwargs = self._parent_connection.recv()
                method = getattr(self._display_controller, method_name)
                method(*args, **kwargs)
            except EOFError:
                if self._started:
                    raise

    def stop(self):
        self._parent_connection.close()
        self._started = False

