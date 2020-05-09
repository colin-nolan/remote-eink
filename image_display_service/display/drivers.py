from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Image:
    """
    TODO
    """
    identifier: str
    data: bytes


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
        self._sleep()
        self._sleeping = True

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
