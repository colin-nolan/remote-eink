from typing import Dict, Any, Iterable, Collection, Sequence, Iterator, Tuple, Optional

import logging
from abc import abstractmethod, ABCMeta
from enum import unique, Enum, auto

from remote_eink.events import EventListenerController
from remote_eink.models import Image, ImageType

_logger = logging.getLogger(__name__)

ImageTypeToPillowFormat = {
    ImageType.JPG: "JPEG",
    ImageType.PNG: "PNG",
}
# TODO: assert all captured


@unique
class ImageTransformerEvent(Enum):
    """
    TODO
    """
    ACTIVATE_STATE = auto()
    TRANSFORM = auto()


class InvalidConfigurationError(ValueError):
    """
    TODO
    """
    def __init__(self, configuration: Any, details: str = ""):
        if details != "":
            details = f" ({details})"
        super().__init__(f"Invalid configuration{details}: {configuration}")
        self.configuration = configuration


class ImageTransformer(metaclass=ABCMeta):
    """
    TODO
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
        TODO
        :return: TODO
        """

    @abstractmethod
    def load_configuration(self, configuration: Dict[str, Any]):
        """
        Loads the given configuration, where the configuration is in the same form as available through the
        `configuration` property
        :param configuration: configuration to load
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
        self.event_listeners.call_listeners(ImageTransformerEvent.ACTIVATE_STATE, [active])

    def __init__(self, identifier: str, active: bool = True):
        """
        TODO
        :param identifier:
        :param active:
        """
        self._identifier = identifier
        self._active = active
        self.event_listeners = EventListenerController[ImageTransformerEvent]()

    def transform(self, image: Image) -> Image:
        """
        TODO
        :param image:
        :return:
        """
        transformed_image = self._transform(image)
        self.event_listeners.call_listeners(ImageTransformerEvent.TRANSFORM, [image, transformed_image])
        return transformed_image


@unique
class ImageTransformerCollectionEvent(Enum):
    """
    TODO
    """
    ADD = auto()
    REMOVE = auto()


class ImageTransformerCollection(Sequence):
    """
    TODO
    """
    def __init__(self, image_transformers: Sequence[ImageTransformer]):
        self._image_transformers = list(image_transformers)
        self.event_listeners = EventListenerController[ImageTransformer]()

    def __len__(self) -> int:
        return len(self._image_transformers)

    def __iter__(self) -> Iterator[ImageTransformer]:
        """
        TODO: ordering
        :return:
        """
        return iter(self._image_transformers)

    def __contains__(self, x: object) -> bool:
        if not isinstance(x, ImageTransformer):
            return False
        return any(image_transformer == x for image_transformer in self._image_transformers)

    def __getitem__(self, position: int) -> ImageTransformer:
        return self._image_transformers[position]

    def get_by_id(self, image_transformer_id: str) -> Optional[Tuple[ImageTransformer, int]]:
        """
        TODO
        :param image_transformer_id:
        :return:
        """
        for i, image_transformer in enumerate(self._image_transformers):
            if image_transformer.identifier == image_transformer_id:
                return image_transformer, i
        return None

    def get_position(self, image_transformer: ImageTransformer) -> int:
        """
        TODO
        :param image_transformer:
        :return:
        :raises KeyError:
        """
        for i in range(len(self._image_transformers)):
            if self._image_transformers[i] == image_transformer:
                return i
        raise KeyError(f"Image transformer not in collection: {image_transformer}")

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
            raise ValueError("Position must be >= 0")
        self._image_transformers.insert(position, image_transformer)
        self.event_listeners.call_listeners(ImageTransformerCollectionEvent.ADD, [image_transformer, position])

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
        self.event_listeners.call_listeners(ImageTransformerCollectionEvent.REMOVE, [image_transformer, removed])
        return removed
