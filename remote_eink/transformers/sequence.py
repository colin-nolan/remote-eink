from abc import ABCMeta, abstractmethod
from enum import unique, Enum, auto
from typing import Sequence, Optional, Union, Iterator

from remote_eink.events import EventListenerController
from remote_eink.transformers import ImageTransformer
from remote_eink.transformers.base import InvalidPositionError


class ImageTransformerSequence(Sequence[ImageTransformer], metaclass=ABCMeta):
    """
    A sequence of `ImageTransformer`.
    """

    @abstractmethod
    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        """
        Gets an image transformer in the sequence by ID.
        :param image_transformer_id: the ID of the image transformer
        :return: an image transformer with the given ID or `None` if it does not exist
        """

    @abstractmethod
    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        """
        Gets the position of the given image transformer.
        :param image_transformer: the image transformer in the sequence or its ID
        :return: position of the image transformer
        :raises KeyError: when the image transformer is not in the sequence
        """

    @abstractmethod
    def set_position(self, image_transformer: ImageTransformer, position: int):
        """
        Sets the position of the given image transformer in the sequence.
        :param image_transformer: image transformer that must be in the sequence (use `add` if it's not)
        :param position: position in sequence, where 0 is the start. If the position is larger than the size of the
        sequence, the image transformer will be put in the last position
        :raises InvalidPositionError: when the position is invalid
        :raises KeyError: when the image transformer is not in the sequence
        """

    @abstractmethod
    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        """
        Adds the given image transformer.
        :param image_transformer: transformer to add
        :param position: position in the sequence
        :return:
        """

    @abstractmethod
    def remove(self, image_transformer: ImageTransformer) -> bool:
        """
        Remove the given image transformer.
        :param image_transformer: the transformer to remove
        :return: `True` if was in collection and removed else `False` if wasn't in collection
        """


class SimpleImageTransformerSequence(ImageTransformerSequence):
    """
    A basic sequence of image transformers.
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

    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        for i, image_transformer in enumerate(self._image_transformers):
            if image_transformer.identifier == image_transformer_id:
                return image_transformer
        return None

    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        identifier = image_transformer if isinstance(image_transformer, str) else image_transformer.identifier
        for i in range(len(self._image_transformers)):
            if self._image_transformers[i].identifier == identifier:
                return i
        raise KeyError(f"Image transformer not in collection: {image_transformer}")

    def set_position(self, image_transformer: ImageTransformer, position: int):
        if image_transformer not in self._image_transformers:
            raise KeyError(f"Image transformer not in sequence: {image_transformer}")
        if position < 0:
            raise InvalidPositionError(f"Position must be at least 0: {position}")
        self._image_transformers.remove(image_transformer)
        self._image_transformers.insert(position, image_transformer)

    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        if self.get_by_id(image_transformer.identifier) is not None:
            raise ValueError(f"Image transformer with same ID already exists: {image_transformer.identifier}")
        if position is None:
            position = len(self._image_transformers)
        if position < 0:
            raise InvalidPositionError("Position must be >= 0")
        self._image_transformers.insert(position, image_transformer)
        self.event_listeners.call_listeners(SimpleImageTransformerSequence.Event.ADD, [image_transformer, position])

    def remove(self, image_transformer: ImageTransformer) -> bool:
        removed = False
        try:
            self._image_transformers.remove(image_transformer)
            removed = True
        except ValueError:
            pass
        self.event_listeners.call_listeners(SimpleImageTransformerSequence.Event.REMOVE, [image_transformer, removed])
        return removed
