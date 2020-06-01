from abc import ABCMeta, abstractmethod
from enum import unique, Enum, auto
from typing import Optional

from remote_eink.events import EventListenerController
from remote_eink.models import Image


class DisplayDriver(metaclass=ABCMeta):
    """
    TODO
    """
    @property
    @abstractmethod
    def sleeping(self) -> bool:
        """
        TODO
        :return:
        """

    @property
    @abstractmethod
    def image(self) -> Optional[Image]:
        """
        TODO
        :return:
        """

    @abstractmethod
    def display(self, image: Image):
        """
        TODO
        :param image:
        :return:
        """

    @abstractmethod
    def clear(self):
        """
        TODO
        :return:
        """

    @abstractmethod
    def sleep(self):
        """
        TODO
        :return:
        """

    @abstractmethod
    def wake(self):
        """
        TODO
        :return:
        """


class ListenableDisplayDriver(DisplayDriver):
    """
    TODO
    """
    @unique
    class Event(Enum):
        DISPLAY = auto()
        CLEAR = auto()
        SLEEP = auto()
        WAKE = auto()
        RESET_SLEEP_TIMER = auto()

    @property
    @abstractmethod
    def event_listeners(self) -> EventListenerController["ListenableDisplayDriver.Event"]:
        """
        TODO
        :return:
        """


class BaseDisplayDriver(ListenableDisplayDriver, metaclass=ABCMeta):
    """
    TODO
    """
    @property
    def sleeping(self) -> bool:
        return self._sleeping

    @property
    def image(self) -> Optional[Image]:
        return self._image

    @property
    def event_listeners(self) -> EventListenerController[ListenableDisplayDriver.Event]:
        return self._event_listeners

    def __init__(self, sleeping: bool = False, image: Optional[Image] = None):
        """
        TODO
        :param sleeping:
        """
        self._event_listeners = EventListenerController[ListenableDisplayDriver.Event]()
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
        self.event_listeners.call_listeners(ListenableDisplayDriver.Event.DISPLAY, [image])

    def clear(self):
        """
        TODO
        :return:
        """
        self._clear()
        self._image = None
        self.event_listeners.call_listeners(ListenableDisplayDriver.Event.CLEAR)

    def sleep(self):
        """
        TODO
        :return:
        """
        if not self.sleeping:
            self._sleep()
            self._sleeping = True
            self.event_listeners.call_listeners(ListenableDisplayDriver.Event.SLEEP)

    def wake(self):
        """
        TODO
        :return:
        """
        if self.sleeping:
            self._wake()
            self._sleeping = False
            self.event_listeners.call_listeners(ListenableDisplayDriver.Event.WAKE)

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


class DummyDisplayDriver(BaseDisplayDriver):
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
