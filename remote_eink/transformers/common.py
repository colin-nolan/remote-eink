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


class ImageTransformer(metaclass=ABCMeta):
    """
    TODO
    """
    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """
        TODO
        :return:
        """

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool):
        self._active = active
        self.event_listeners.call_listeners(ImageTransformerEvent.ACTIVATE_STATE, [active])

    def __init__(self, active: bool = True):
        """
        TODO
        :param active:
        """
        self._active = active
        self.event_listeners = EventListenerController()

    @abstractmethod
    def transform(self, image: Image) -> Image:
        """
        TODO
        :param image:
        :return:
        """
