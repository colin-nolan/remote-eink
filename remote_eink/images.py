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
    Image that can be displayed on a device.
    """

    @property
    @abstractmethod
    def data(self) -> bytes:
        """
        Data that makes up the image.
        :return: bytes of data
        """

    @property
    def identifier(self) -> str:
        """
        Image identifier.
        :return: identifier
        """
        return self._identifier

    @property
    def type(self) -> ImageType:
        """
        Type of the image (e.g. png).
        :return: image type
        """
        return self._type

    # TODO: handle rotation as broader metadata
    @property
    def rotation(self) -> float:
        """
        The rotation of the image in degrees (clockwise).
        :return: rotation
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
    An image based on data stored in memory.
    """

    @property
    def data(self) -> bytes:
        return self._data

    def __init__(self, identifier: str, data: bytes, image_type: ImageType, *, rotation: float = 0):
        """
        Constructor.
        :param identifier: see `Image.__init__`
        :param data: image data
        :param image_type: see `Image.__init__`
        """
        super().__init__(identifier, image_type, rotation=rotation)
        self._data = data


class FunctionBasedImage(Image):
    """
    Immutable model of an image attained via an `ImageDataReader` (callable).
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
