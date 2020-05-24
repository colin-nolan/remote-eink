from typing import Dict, Any, Sequence, Iterator, Tuple, Optional

import logging
from abc import abstractmethod, ABCMeta
from enum import unique, Enum, auto

from remote_eink.events import EventListenerController
from remote_eink.models import Image, ImageType

_logger = logging.getLogger(__name__)

ImageTypeToPillowFormat = {
    ImageType.BMP: "BMP",
    ImageType.JPG: "JPEG",
    ImageType.PNG: "PNG",
    ImageType.WEBP: "WEBP"
}
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
    @unique
    class Event(Enum):
        ACTIVATE_STATE = auto()
        TRANSFORM = auto()

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
        Description of the transformer
        :return: description
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

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool):
        self._active = active
        self.event_listeners.call_listeners(ImageTransformer.Event.ACTIVATE_STATE, [active])

    def __init__(self, identifier: str, active: bool = True):
        """
        Constructor
        :param identifier: transformer identifier
        :param active: whether the transformer is active
        """
        self._identifier = identifier
        self._active = active
        self.event_listeners = EventListenerController[ImageTransformer.Event]()

    def transform(self, image: Image) -> Image:
        """
        Applies transformation to the given image.
        :param image: image to transform (not modified)
        :return: new image with the transform
        """
        transformed_image = self._transform(image)
        self.event_listeners.call_listeners(ImageTransformer.Event.TRANSFORM, [image, transformed_image])
        return transformed_image


class ImageTransformerSequence(Sequence):
    """
    Sequence of image transformers.
    """
    @unique
    class Event(Enum):
        ADD = auto()
        REMOVE = auto()

    def __init__(self, image_transformers: Sequence[ImageTransformer]):
        self._image_transformers = list(image_transformers)
        self.event_listeners = EventListenerController[ImageTransformer]()

    def __len__(self) -> int:
        return len(self._image_transformers)

    def __iter__(self) -> Iterator[ImageTransformer]:
        return iter(self._image_transformers)

    def __contains__(self, x: object) -> bool:
        if not isinstance(x, ImageTransformer):
            return False
        return any(image_transformer == x for image_transformer in self._image_transformers)

    def __getitem__(self, position: int) -> ImageTransformer:
        return self._image_transformers[position]

    def get_by_id(self, image_transformer_id: str) -> Optional[Tuple[ImageTransformer, int]]:
        """
        Gets an image transformer in the sequence by ID.
        :param image_transformer_id: the ID of the image transformer
        :return: tuple where the first element is the matched image transformer and the second is its position in the
        sequence. If an image transformer with the given ID does not exist in the sequenece, `None` will be returned
        """
        for i, image_transformer in enumerate(self._image_transformers):
            if image_transformer.identifier == image_transformer_id:
                return image_transformer, i
        return None

    def get_position(self, image_transformer: ImageTransformer) -> int:
        """
        Gets the position of the given image transformer.
        :param image_transformer: the image transformer in the sequence
        :return: position of the image transformer
        :raises KeyError: when the image transformer is not in the sequence
        """
        for i in range(len(self._image_transformers)):
            if self._image_transformers[i] == image_transformer:
                return i
        raise KeyError(f"Image transformer not in collection: {image_transformer}")

    def set_position(self, image_transformer: ImageTransformer, position: int):
        """
        Sets the position of the given image transformer in the sequence.
        :param image_transformer: image transformer that must be in the sequence (use `add` if it's not)
        :param position: position in sequence, where 0 is the start. If the position is larger than the size of the
        sequence, the image transformer will be put in the last position
        :raises InvalidPositionError: when the position is invalid
        :raises KeyError: when the image transformer is not in the sequence
        """
        if image_transformer not in self._image_transformers:
            raise KeyError(f"Image transformer not in sequence: {image_transformer}")
        if position < 0:
            raise InvalidPositionError(f"Position must be at least 0: {position}")
        self._image_transformers.remove(image_transformer)
        self._image_transformers.insert(position, image_transformer)

    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        """
        Adds the given image transformer.
        :param image_transformer: transformer to add
        :param position: position in the sequence
        :return:
        """
        if self.get_by_id(image_transformer.identifier) is not None:
            raise ValueError(f"Image transformer with same ID already exists: {image_transformer.identifier}")
        if position is None:
            position = len(self._image_transformers)
        if position < 0:
            raise InvalidPositionError("Position must be >= 0")
        self._image_transformers.insert(position, image_transformer)
        self.event_listeners.call_listeners(ImageTransformerSequence.Event.ADD, [image_transformer, position])

    def remove(self, image_transformer: ImageTransformer) -> bool:
        """
        Remove the given image transformer.
        :param image_transformer: the transformer to remove
        :return: `True` if was in collection and removed else `False` if wasn't in collection
        """
        removed = False
        try:
            self._image_transformers.remove(image_transformer)
            removed = True
        except ValueError:
            pass
        self.event_listeners.call_listeners(ImageTransformerSequence.Event.REMOVE, [image_transformer, removed])
        return removed
