from abc import ABCMeta, abstractmethod
from enum import unique, Enum, auto
from typing import Optional

from remote_eink.events import EventListenerController
from remote_eink.models import Image


@unique
class DisplayDriverEvent(Enum):
    """
    TODO
    """
    DISPLAY = auto()
    CLEAR = auto()
    SLEEP = auto()
    WAKE = auto()


class DisplayDriver(metaclass=ABCMeta):
    """
    TODO
    """
    @property
    def sleeping(self) -> bool:
        return self._sleeping

    @property
    def image(self) -> Optional[Image]:
        return self._image

    def __init__(self, sleeping: bool = False, image: Optional[Image] = None):
        """
        TODO
        :param sleeping:
        """
        self.event_listeners = EventListenerController[DisplayDriverEvent]()
        self._sleeping = sleeping
        self._image = None
        if image:
            self.display(image)

    def display(self, image: Image):
        """
        TODO
        :param image:
        :return:
        """
        if self.sleeping:
            self.wake()
        self._display(image.data)
        self._image = image
        self.event_listeners.call_listeners(DisplayDriverEvent.DISPLAY, [image])

    def clear(self):
        """
        TODO
        :return:
        """
        self._clear()
        self._image = None
        self.event_listeners.call_listeners(DisplayDriverEvent.CLEAR)

    def sleep(self):
        """
        TODO
        :return:
        """
        if not self.sleeping:
            self._sleep()
            self._sleeping = True
        self.event_listeners.call_listeners(DisplayDriverEvent.SLEEP)

    def wake(self):
        """
        TODO
        :return:
        """
        if self.sleeping:
            self._wake()
            self._sleeping = False
        self.event_listeners.call_listeners(DisplayDriverEvent.WAKE)

    @abstractmethod
    def _display(self, image_data: bytes):
        """
        TODO
        :param image_data:
        :return:
        """

    @abstractmethod
    def _clear(self):
        """
        TODO
        :return:
        """

    @abstractmethod
    def _sleep(self):
        """
        TODO
        :return:
        """

    @abstractmethod
    def _wake(self):
        """
        TODO
        :return:
        """


class DummyDisplayDriver(DisplayDriver):
    """
    TODO
    """
    def _display(self, image_data: bytes):
        pass

    def _clear(self):
        pass

    def _sleep(self):
        pass

    def _wake(self):
        pass
