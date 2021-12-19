from abc import ABCMeta, abstractmethod
from enum import unique, Enum
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


class Image(metaclass=ABCMeta):
    """
    TODO
    """

    @property
    @abstractmethod
    def data(self) -> bytes:
        """
        TODO
        :return:
        """

    @property
    def identifier(self) -> str:
        """
        TODO
        :return:
        """
        return self._identifier

    @property
    def type(self) -> ImageType:
        """
        TODO
        :return:
        """
        return self._type

    @property
    def rotation(self) -> float:
        """
        TODO
        :return:
        """
        return self._rotation

    def __init__(self, identifier: str, image_type: ImageType, *, rotation: float = 0):
        """
        Constructor.
        :param identifier: image identifier
        :param image_type: the type of the image (e.g. PNG)
        :param rotation: clockwise rotation of the image in degrees, relative to upright
        """
        self._identifier = identifier
        self._type = image_type
        self._rotation = rotation

    def __repr__(self) -> str:
        return repr(dict(identifier=self.identifier))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Image):
            return False
        if other.identifier != self.identifier:
            return False
        return other.data == self.data

    def __hash__(self) -> int:
        return hash(self.identifier)


class DataBasedImage(Image):
    """
    TODO
    """

    @property
    def data(self) -> bytes:
        return self._data

    def __init__(self, identifier: str, data: bytes, image_type: ImageType, *, rotation: float = 0):
        """
        TODO
        :param identifier: see `Image.__init__`
        :param data: image data
        :param image_type: see `Image.__init__`
        """
        super().__init__(identifier, image_type, rotation=rotation)
        self._data = data


class FunctionBasedImage(Image):
    """
    Immutable model of an image.
    """

    @property
    def data(self) -> bytes:
        return self._data_reader()

    def __init__(self, identifier: str, data_reader: ImageDataReader, image_type: ImageType, *, rotation: float = 0):
        """
        Constructor.
        :param identifier: see `Image.__init__`
        :param data_reader: (reusable) callable that can be used to read a copy of the image data
        :param image_type: see `Image.__init__`
        """
        super().__init__(identifier, image_type, rotation=rotation)
        self._data_reader = data_reader
