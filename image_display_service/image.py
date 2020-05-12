from enum import unique, Enum, auto
from typing import Any, Callable

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


class Image:
    """
    Image that can be displayed.
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

    def __init__(self, identifier: str, data_reader: ImageDataReader, image_type: ImageType,
                 cache_data: bool = True):
        """
        Constructor.
        :param identifier: image identifier
        :param data_reader: (reusable) callable that can be used to read a copy of the image data
        :param image_type: the type of the image (e.g. PNG)
        :param cache_data: whether to cache the data when read using the reader
        """
        self._identifier = identifier
        self._data_reader = data_reader
        self.type = image_type
        self._cache_data = cache_data
        self._cached = None

    def __repr__(self) -> str:
        return repr(dict(identifier=self.identifier, data=self.data))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if other.identifier != self.identifier:
            return False
        return other.data == self.data

    def __hash__(self) -> int:
        return hash(self.identifier)
