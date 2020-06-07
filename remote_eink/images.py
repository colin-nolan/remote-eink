from abc import ABCMeta, abstractmethod
from enum import unique, Enum
from typing import Any, Callable

from remote_eink.multiprocess import ProxyObject

ImageDataReader = Callable[[], bytes]


@unique
class ImageType(Enum):
    """
    Image type.
    """
    BMP = "bmp"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"


class Image(metaclass=ABCMeta):
    """
    TODO
    """
    @property
    @abstractmethod
    def identifier(self) -> str:
        """
        TODO
        :return:
        """

    @property
    @abstractmethod
    def data(self) -> bytes:
        """
        TODO
        :return:
        """

    @property
    @abstractmethod
    def type(self) -> ImageType:
        """
        TODO
        :return:
        """

    def __repr__(self) -> str:
        return repr(dict(identifier=self.identifier, data=self.data))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Image):
            return False
        if other.identifier != self.identifier:
            return False
        return other.data == self.data

    def __hash__(self) -> int:
        return hash(self.identifier)


class SimpleImage(Image):
    """
    Immutable model of an image.
    """
    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def cache_data(self) -> bool:
        return self._cache_data

    @cache_data.setter
    def cache_data(self, cache_on: bool):
        if not cache_on:
            self._cached = None
        self._cache_data = cache_on

    @property
    def data(self) -> bytes:
        if self._cached:
            return self._cached
        data = self._data_reader()
        if self.cache_data:
            self._cached = data
        return data

    @property
    def type(self) -> ImageType:
        return self._type

    def __init__(self, identifier: str, data_reader: ImageDataReader, image_type: ImageType,
                 cache_data: bool = False):
        """
        Constructor.
        :param identifier: image identifier
        :param data_reader: (reusable) callable that can be used to read a copy of the image data
        :param image_type: the type of the image (e.g. PNG)
        :param cache_data: whether to cache the data when read using the reader
        """
        self._identifier = identifier
        self._data_reader = data_reader
        self._type = image_type
        self._cache_data = cache_data
        self._cached = None


class ProxyImage(Image, ProxyObject):
    """
    TODO
    """
    @property
    def identifier(self) -> str:
        return self._communicate("identifier")

    @property
    def data(self) -> bytes:
        return self._communicate("data")

    @property
    def type(self) -> ImageType:
        return self._communicate("type")
