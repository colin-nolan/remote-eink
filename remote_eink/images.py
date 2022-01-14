import hashlib
from abc import ABCMeta, abstractmethod
from enum import unique, Enum
from types import MappingProxyType
from typing import Any, Callable, Dict

from typing_extensions import Self

ImageDataReader = Callable[[], bytes]
ImageMetadata = Dict[str, str | int | float | Self]


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

    @property
    def metadata(self) -> ImageMetadata:
        """
        Metadata associated to the image (e.g. rotation).
        :return: metadata
        """
        return self._metadata

    def __init__(self, identifier: str, image_type: ImageType, *, metadata: ImageMetadata = MappingProxyType({})):
        """
        Constructor.
        :param identifier: image identifier
        :param image_type: the type of the image (e.g. PNG)
        :param metadata: metadata associated to the image
        """
        if not isinstance(image_type, ImageType):
            raise TypeError(f"image_type was of incorrect type: {type(image_type)}")
        if metadata == MappingProxyType({}):
            metadata = {}
        self._identifier = identifier
        self._type = image_type
        self._metadata = metadata

    def __repr__(self) -> str:

        return repr(
            dict(
                identifier=self.identifier,
                metadata=self.metadata,
                image_type=self.type,
                data_md5=hashlib.md5(self.data).hexdigest(),
            )
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Image):
            return False
        if other.identifier != self.identifier:
            return False
        if other.metadata != self.metadata:
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

    def __init__(
        self, identifier: str, data: bytes, image_type: ImageType, metadata: ImageMetadata = MappingProxyType({})
    ):
        """
        Constructor.
        :param identifier: see `Image.__init__`
        :param data: image data
        :param image_type: see `Image.__init__`
        :param metadata: see `Image.__init__`
        """
        super().__init__(identifier, image_type, metadata=metadata)
        self._data = data


class FunctionBasedImage(Image):
    """
    Immutable model of an image attained via an `ImageDataReader` (callable).
    """

    @property
    def data(self) -> bytes:
        return self._data_reader()

    def __init__(
        self,
        identifier: str,
        data_reader: ImageDataReader,
        image_type: ImageType,
        metadata: ImageMetadata = MappingProxyType({}),
    ):
        """
        Constructor.
        :param identifier: see `Image.__init__`
        :param data_reader: (reusable) callable that can be used to read a copy of the image data
        :param image_type: see `Image.__init__`
        :param metadata: see `Image.__init__`
        """
        super().__init__(identifier, image_type, metadata=metadata)
        self._data_reader = data_reader
