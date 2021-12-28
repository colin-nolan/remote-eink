from typing import Dict, Any, Optional, Callable

import logging
from abc import abstractmethod, ABCMeta
from enum import unique, Enum, auto
from uuid import uuid4

from remote_eink.events import EventListenerController
from remote_eink.images import Image, ImageType

logger = logging.getLogger(__name__)

ImageTypeToPillowFormat = {ImageType.BMP: "BMP", ImageType.JPG: "JPEG", ImageType.PNG: "PNG", ImageType.WEBP: "WEBP"}
assert len(ImageTypeToPillowFormat) == len(ImageType)


class InvalidConfigurationError(ValueError):
    def __init__(self, configuration: Any, details: str = ""):
        if details != "":
            details = f" ({details})"
        super().__init__(f"Invalid configuration{details}: {configuration}")
        self.configuration = configuration


class InvalidPositionError(ValueError):
    def __init__(self, position: Any):
        super().__init__(f"Invalid position: {position}")
        self.position = position


class ImageTransformer(metaclass=ABCMeta):
    """
    Image transformer.
    """

    @property
    @abstractmethod
    def active(self) -> bool:
        """
        Whether the transformer is active.
        :return: active status
        """

    @active.setter
    @abstractmethod
    def active(self, active: bool):
        """
        Sets the active status of the transformer.
        :param active: active status where `True` is active
        """

    @property
    @abstractmethod
    def configuration(self) -> Dict[str, Any]:
        """
        Transformer's configuration in a JSON (or similar) serialisable form.
        :return: transformer's configuration
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description of the transformer.
        :return: description
        """

    @property
    @abstractmethod
    def identifier(self) -> str:
        """
        Identifier for the transformer.
        :return: identifier
        """

    @abstractmethod
    def modify_configuration(self, configuration: Dict[str, Any]):
        """
        Modifies the current configuration using the given configuration.
        :param configuration: configuration in the same form as available through the `configuration` property
        :raises InvalidConfigurationError: raised if the configuration is invalid
        """

    @abstractmethod
    def _transform(self, image: Image) -> Image:
        """
        Applies transform to the given image and returns the result as a new image.
        :param image: image to apply transform to
        :return: resulting image
        """

    def transform(self, image: Image) -> Image:
        """
        Applies transformation to the given image.
        :param image: image to transform (not modified)
        :return: new image with the transform
        """
        return self._transform(image)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ImageTransformer):
            return False
        if other.identifier != self.identifier:
            return False
        if other.configuration != self.configuration:
            return False
        if other.active != self.active:
            return False
        return True

    def __hash__(self) -> hash:
        return hash(self.identifier)


class BaseImageTransformer(ImageTransformer, metaclass=ABCMeta):
    """
    Image transformer.
    """

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool):
        self._active = active

    @property
    def identifier(self) -> str:
        return self._identifier

    def __init__(self, identifier: str, active: bool = True):
        """
        Constructor.
        :param identifier: transformer identifier
        :param active: whether the transformer is active
        """
        self._identifier = identifier
        self._active = active


class ListenableImageTransformer(ImageTransformer):
    """
    Wraps an image transformer to make it listenable.
    """

    @unique
    class Event(Enum):
        ACTIVATE_STATE = auto()
        TRANSFORM = auto()

    @property
    def active(self) -> bool:
        return self._image_transformer.active

    @active.setter
    def active(self, active: bool):
        self._image_transformer.active = active
        self.event_listeners.call_listeners(ListenableImageTransformer.Event.ACTIVATE_STATE, [active])

    @property
    def configuration(self) -> Dict[str, Any]:
        return self._image_transformer.configuration

    @property
    def description(self) -> str:
        return self._image_transformer.description

    @property
    def identifier(self) -> str:
        return self._image_transformer.identifier

    def __init__(self, image_transformer: ImageTransformer):
        """
        Constructor.
        :param image_transformer: the image transformer to wrap
        """
        self._image_transformer = image_transformer
        self.event_listeners = EventListenerController[ListenableImageTransformer.Event]()

    def modify_configuration(self, configuration: Dict[str, Any]):
        return self._image_transformer.modify_configuration(configuration)

    def _transform(self, image: Image) -> Image:
        transformed_image = self._image_transformer._transform(image)
        self.event_listeners.call_listeners(ListenableImageTransformer.Event.TRANSFORM, [image, transformed_image])
        return transformed_image


class SimpleImageTransformer(BaseImageTransformer):
    """
    Simple image transformer.
    """

    @property
    def configuration(self) -> Dict[str, Any]:
        return self._configuration

    @property
    def description(self) -> str:
        return self._description

    def __init__(
        self,
        transformer: Optional[Callable[[Image], Image]] = None,
        active: bool = True,
        configuration: Optional[Any] = None,
        description: Optional[str] = None,
        identifier: str = None,
    ):
        super().__init__(identifier if identifier is not None else str(uuid4()), active)
        self._transformer = transformer if transformer is not None else lambda image: image
        self._configuration = configuration if configuration is not None else {}
        self._description = description if description is not None else ""

    def modify_configuration(self, configuration: Dict[str, Any]):
        if "invalid-config-property" in configuration:
            raise InvalidConfigurationError(configuration)
        self._configuration = configuration

    def _transform(self, image: Image) -> Image:
        return self._transformer(image)


