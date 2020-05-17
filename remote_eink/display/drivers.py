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


class BaseDisplayDriver(DisplayDriver, metaclass=ABCMeta):
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

    def clear(self):
        """
        TODO
        :return:
        """
        self._clear()
        self._image = None

    def sleep(self):
        """
        TODO
        :return:
        """
        if not self.sleeping:
            self._sleep()
            self._sleeping = True

    def wake(self):
        """
        TODO
        :return:
        """
        if self.sleeping:
            self._wake()
            self._sleeping = False

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


@unique
class DisplayDriverEvent(Enum):
    """
    TODO
    """
    DISPLAY = auto()
    CLEAR = auto()
    SLEEP = auto()
    WAKE = auto()


class ListenableDisplayDriver(DisplayDriver):
    """
    TODO
    """

    @property
    def sleeping(self) -> bool:
        return self._display_driver.sleeping

    @property
    def image(self) -> Optional[Image]:
        return self._display_driver.image

    def __init__(self, display_driver: DisplayDriver):
        """
        TODO
        :param display_driver:
        """
        self._display_driver = display_driver
        self.event_listeners = EventListenerController[DisplayDriverEvent]()

    def display(self, image: Image):
        self._display_driver.display(image)
        self.event_listeners.call_listeners(DisplayDriverEvent.DISPLAY, [image])

    def clear(self):
        self._display_driver.clear()
        self.event_listeners.call_listeners(DisplayDriverEvent.CLEAR)

    def sleep(self):
        self._display_driver.sleep()
        self.event_listeners.call_listeners(DisplayDriverEvent.SLEEP)

    def wake(self):
        self._display_driver.wake()
        self.event_listeners.call_listeners(DisplayDriverEvent.WAKE)
