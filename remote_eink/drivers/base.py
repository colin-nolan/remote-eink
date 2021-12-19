from abc import ABCMeta, abstractmethod
from enum import auto, unique, Enum
from typing import Optional

from remote_eink.events import EventListenerController
from remote_eink.images import Image


class DisplayDriver(metaclass=ABCMeta):
    """
    Device display driver.
    """

    @property
    @abstractmethod
    def sleeping(self) -> bool:
        """
        Get whether the device is sleeping.
        :return: whether the device is sleeping
        """

    @property
    @abstractmethod
    def image(self) -> Optional[Image]:
        """
        Gets the image that the device is displaying.
        :return: the image being display or `None` if no image displayed
        """

    @image.setter
    @abstractmethod
    def image(self, image: Optional[Image]):
        """
        Sets the image that the device is displaying.
        """

    @abstractmethod
    def sleep(self):
        """
        Sleep the device (if possible).
        """

    @abstractmethod
    def wake(self):
        """
        Wake the device.
        """

    def clear(self):
        """
        Clear the displayed image.
        """
        self.display(None)

    def display(self, image: Optional[Image]):
        """
        Display the given image (alternative to `self.image = image`.
        :param image: the image to display
        """
        self.image = image


class BaseDisplayDriver(DisplayDriver, metaclass=ABCMeta):
    """
    TODO

    Not thread safe.
    """

    @property
    def sleeping(self) -> bool:
        return self._sleeping

    @property
    def image(self) -> Optional[Image]:
        return self._image

    @image.setter
    def image(self, image: Optional[Image]):
        if self.image != image:
            if self.sleeping:
                self.wake()
            if image is not None:
                self._display(image.data)
            else:
                self._clear()
            self._image = image

    def __init__(self, sleeping: bool = False, image: Optional[Image] = None):
        """
        Constructor.
        :param sleeping: whether the device is currently sleeping.
        :param image: image to display initially
        """
        self._sleeping = sleeping
        self._image = None
        self.image = image

    def clear(self):
        """
        TODO
        :return:
        """
        self._clear()
        super().clear()

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


class ListenableDisplayDriver(DisplayDriver):
    """
    Listenable interface composed on a display driver.
    """

    @unique
    class Event(Enum):
        DISPLAY = auto()
        CLEAR = auto()
        SLEEP = auto()
        WAKE = auto()

    @property
    def sleeping(self) -> bool:
        return self._display_driver.sleeping

    @property
    def image(self) -> Optional[Image]:
        return self._display_driver.image

    @image.setter
    def image(self, image: Optional[Image]):
        self._display_driver.display(image)
        self.event_listeners.call_listeners(ListenableDisplayDriver.Event.DISPLAY, [image])

    def __init__(self, display_driver: DisplayDriver):
        """
        Constructor.
        :param display_driver: underlying display driver to create listenable interface to
        """
        self._display_driver = display_driver
        self.event_listeners = EventListenerController["ListenableDisplayDriver.Event"]()

    def clear(self):
        self._display_driver.clear()
        self.event_listeners.call_listeners(ListenableDisplayDriver.Event.CLEAR)

    def sleep(self):
        if not self.sleeping:
            self._display_driver.sleep()
            self.event_listeners.call_listeners(ListenableDisplayDriver.Event.SLEEP)

    def wake(self):
        if self.sleeping:
            self._display_driver.wake()
            self.event_listeners.call_listeners(ListenableDisplayDriver.Event.WAKE)
