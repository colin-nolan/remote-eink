from abc import abstractmethod, ABCMeta
from enum import unique, Enum, auto
from threading import Timer
from typing import Optional

from remote_eink.drivers.base import DisplayDriver, ListenableDisplayDriver
from remote_eink.events import EventListenerController
from remote_eink.images import Image
from remote_eink.storage.image.base import ImageStore
from remote_eink.transformers import ImageTransformerSequence


class ImageNotFoundError(ValueError):
    """
    Raised when an image cannot be found when expected.
    """

    def __init__(self, image_id: str):
        super().__init__(f"Image cannot be found: {image_id}")


class DisplayController(metaclass=ABCMeta):
    """
    Display controller.
    """

    @property
    @abstractmethod
    def friendly_type_name(self) -> str:
        """
        Gets the friendly name of the display controller type.
        :return: name of display controller type
        """

    @property
    @abstractmethod
    def identifier(self) -> str:
        """
        Unique identifier of the display controller.
        :return: display controller's unique identifier
        """

    @property
    @abstractmethod
    def current_image(self) -> Optional[Image]:
        """
        Image currently been displayed on the display.
        :return: displayed image or `None` if no image is being displayed. Image will not have any transforms applied
                 (see `apply_image_transforms`)
        """

    @property
    @abstractmethod
    def driver(self) -> DisplayDriver:
        """
        Underlying display device driver.
        :return: display device driver
        """

    @property
    @abstractmethod
    def image_store(self) -> ImageStore:
        """
        Displays image storage
        :return: image storage
        """

    @property
    @abstractmethod
    def image_transformers(self) -> ImageTransformerSequence:
        """
        Sequence of image transformers that will be applied to the image before it is given to the device driver for
        display.
        :return: sequence of image transformers (first in sequence is applied first)
        """

    @abstractmethod
    def display(self, image_id: str):
        """
        Displays the image with the given ID.
        :param image_id: ID of stored image
        :raises ImageNotFoundError: iof an image with the given ID is not found in the image store
        """

    @abstractmethod
    def clear(self):
        """
        Clears the display.
        """

    @abstractmethod
    def apply_image_transforms(self, image: Image) -> Image:
        """
        Apply image transforms (defined by the image transformers sequence) to the given image.
        :param image: image to apply transforms (not modified)
        :return: new, transformed image
        """


# TODO: why is this abstract but listenable storage is not?
class ListenableDisplayController(DisplayController, metaclass=ABCMeta):
    """
    Display controller with listenable events.
    """

    @unique
    class Event(Enum):
        DISPLAY_CHANGE = auto()

    @property
    @abstractmethod
    def driver(self) -> ListenableDisplayDriver:
        """
        See `DisplayController.driver`.
        :return: see `DisplayController.driver`.
        """

    @property
    @abstractmethod
    def event_listeners(self) -> EventListenerController["ListenableDisplayController.Event"]:
        """
        Gets event listener controller.
        :return: event listener controller
        """


class SleepyDisplayController(ListenableDisplayController):
    """
    Listenable display controller that sleeps the display driver a period of time after the display is updated.
    """

    @property
    def friendly_type_name(self) -> str:
        return f"Sleepy{self._display_controller.friendly_type_name}"

    @property
    def identifier(self) -> str:
        return self._display_controller.identifier

    @property
    def current_image(self) -> Optional[Image]:
        return self._display_controller.current_image

    @property
    def driver(self) -> DisplayDriver:
        return self._display_controller.driver

    @property
    def image_store(self) -> ImageStore:
        return self._display_controller.image_store

    @property
    def image_transformers(self) -> ImageTransformerSequence:
        return self._display_controller.image_transformers

    @property
    def event_listeners(self) -> EventListenerController["ListenableDisplayController.Event"]:
        return self._display_controller.event_listeners

    def display(self, image_id: str):
        self._display_controller.display(image_id)

    def clear(self):
        self._display_controller.clear()

    def apply_image_transforms(self, image: Image) -> Image:
        return self._display_controller.apply_image_transforms(image)

    def __init__(self, display_controller: ListenableDisplayController, sleep_after_seconds: float = 300):
        """
        Constructor.
        :param display_controller: the listenable display controller to wrap
        :param sleep_after_seconds: the number of seconds after the display changes to sleep the device
        """
        self._display_controller = display_controller
        self._sleep_after_seconds = sleep_after_seconds

        self.started = False
        self._sleep_timer: Optional[Timer] = None

        self.event_listeners.add_listener(self._restart_sleep_timer, ListenableDisplayController.Event.DISPLAY_CHANGE)

    def start(self):
        self.started = True

    def stop(self):
        if self._sleep_timer is not None:
            self._sleep_timer.cancel()
            self._sleep_timer = None
        self.started = False

    def _restart_sleep_timer(self):
        if self.started:
            if self._sleep_timer is not None:
                self._sleep_timer.cancel()
            self._sleep_timer = Timer(self._sleep_after_seconds, lambda: self.driver.sleep())
            self._sleep_timer.start()
