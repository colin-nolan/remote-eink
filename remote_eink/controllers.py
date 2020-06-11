from enum import unique, Enum, auto

from abc import abstractmethod, ABCMeta
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from threading import Timer
from typing import Optional, Sequence
from uuid import uuid4

from remote_eink.drivers.base import DisplayDriver, ListenableDisplayDriver
from remote_eink.events import EventListenerController
from remote_eink.images import Image
from remote_eink.storage.images import ImageStore, ListenableImageStore
from remote_eink.transformers.base import ImageTransformer, ImageTransformerSequence, SimpleImageTransformerSequence

DEFAULT_SECONDS_BETWEEN_CYCLE = float(60 * 60)


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


class BaseDisplayController(DisplayController):
    """
    Display controller.
    """
    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def current_image(self) -> Optional[Image]:
        # The reason why we don't return `self._driver.image` is that the device may be displaying a transformation of
        # the image
        return self._current_image

    @property
    def driver(self) -> ListenableDisplayDriver:
        return self._driver

    @property
    def image_store(self) -> ListenableImageStore:
        return self._image_store

    @property
    def image_transformers(self) -> ImageTransformerSequence:
        return self._image_transformers

    @property
    def event_listeners(self) -> EventListenerController["ListenableDisplayController.Event"]:
        return self._event_listeners

    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_transformers: Sequence[ImageTransformer] = ()):
        """
        Constructor.
        :param driver: display driver
        :param image_store: image store
        :param identifier: driver identifier
        :param image_transformers: image display transformers
        """
        self._identifier = identifier if identifier is not None else str(uuid4())
        self._driver = ListenableDisplayDriver(driver)
        self._current_image = None
        self._image_store = ListenableImageStore(image_store)
        self._image_transformers = SimpleImageTransformerSequence(image_transformers)

        self._display_requested = False
        self._event_listeners = EventListenerController[ListenableDisplayController.Event]()
        self._image_store.event_listeners.add_listener(self._on_remove_image, ListenableImageStore.Event.REMOVE)
        self._driver.event_listeners.add_listener(self._on_clear, ListenableDisplayDriver.Event.CLEAR)
        self._driver.event_listeners.add_listener(self._on_display, ListenableDisplayDriver.Event.DISPLAY)

    def display(self, image_id: str):
        image = self.image_store.get(image_id)
        if image is None:
            raise ImageNotFoundError(image_id)
        if image != self.current_image:
            transformed_image = self.apply_image_transforms(image)
            self._display_requested = True
            try:
                self.driver.display(transformed_image)
            finally:
                self._display_requested = False
            self._current_image = image

    def clear(self):
        self.driver.clear()

    def apply_image_transforms(self, image: Image) -> Image:
        for transformer in self.image_transformers:
            if transformer.active:
                image = transformer.transform(image)
        return image

    def _on_remove_image(self, image_id: str):
        """
        Handler for when an image has been removed from the image store.
        :param image_id: ID of the image that has been removed
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.driver.clear()

    def _on_clear(self):
        """
        Handler for when the display is cleared via the driver.
        """
        assert self.driver.image is None
        self._current_image = None
        self.event_listeners.call_listeners(ListenableDisplayController.Event.DISPLAY_CHANGE)

    def _on_display(self, image: Image):
        """
        Handler for when an image is displayed via the driver.
        :param image: the image that has been displayed
        """
        assert self.driver.image == image
        if not self._display_requested:
            # Driver has been used directly to update - cope with it
            if self.image_store.get(image.identifier) is None:
                self.image_store.add(image)
            self._current_image = image
        self.event_listeners.call_listeners(ListenableDisplayController.Event.DISPLAY_CHANGE)


class CyclableDisplayController(BaseDisplayController):
    """
    Display controller that can cycle through the image that it displays.
    """
    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_transformers: Sequence[ImageTransformer] = ()):
        """
        Constructor.
        :param driver: `BaseDisplayController.__init__`
        :param image_store: `BaseDisplayController.__init__`
        :param identifier: `BaseDisplayController.__init__`
        :param image_transformers: `BaseDisplayController.__init__`
        """
        super().__init__(driver, image_store, identifier, image_transformers)
        self._image_queue = []
        # Note: the superclass converts the image store to a `ListenableImageStore`
        self.image_store.event_listeners.add_listener(
            lambda image: self._add_to_queue(image.identifier), ListenableImageStore.Event.ADD)
        for image in self.image_store.list():
            self._add_to_queue(image.identifier)

    def display_next_image(self) -> Optional[Image]:
        """
        Displays the next image in the image queue.
        :return: image displayed or `None` if no images to display
        """
        if len(self._image_queue) == 0:
            self.driver.clear()
            return None

        image_id = self._image_queue.pop(0)
        image = self.image_store.get(image_id)
        if image is None:
            return self.display_next_image()
        self._image_queue.append(image_id)

        if len(self._image_queue) == 1:
            if self.current_image == image_id:
                return self.current_image
        elif self.current_image and image_id == self.current_image.identifier:
            return self.display_next_image()

        self.display(image_id)
        return image

    def _add_to_queue(self, image_id: str):
        """
        Adds the image with the given ID
        :param image_id:
        :return:
        """
        self._image_queue.append(image_id)

    def _on_remove_image(self, image_id: str):
        if self.current_image and self.current_image.identifier == image_id:
            self.display_next_image()


class AutoCyclingDisplayController(CyclableDisplayController):
    """
    Display controller that auto cycles through images.
    """
    def __init__(self, driver: DisplayDriver, image_store: ImageStore,
                 identifier: Optional[str] = None, image_transformers: Sequence[ImageTransformer] = (),
                 cycle_image_after_seconds: float = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        Constructor.
        :param driver: see `CyclableDisplayController.__init__`
        :param image_store: see `CyclableDisplayController.__init__`
        :param identifier: see `CyclableDisplayController.__init__`
        :param image_transformers: see `CyclableDisplayController.__init__`
        :param cycle_image_after_seconds: the number of seconds before cycling on to the next image
        """
        super().__init__(driver, image_store, identifier, image_transformers)
        self.cycle_image_after_seconds = cycle_image_after_seconds
        self._scheduler = BackgroundScheduler()

    def start(self):
        if self._scheduler.state != STATE_RUNNING:
            self._scheduler.start()
            self._scheduler.add_job(self.display_next_image, "interval", seconds=self.cycle_image_after_seconds)

    def stop(self):
        self._scheduler.remove_all_jobs()
        try:
            self._scheduler.pause()
        except SchedulerNotRunningError:
            pass


class SleepyDisplayController(ListenableDisplayController):
    """
    TODO
    """
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
        TODO
        :param display_controller:
        :param sleep_after_seconds:
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
