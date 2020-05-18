from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

from remote_eink.display.drivers import DisplayDriver, ListenableDisplayDriver, DisplayDriverEvent
from remote_eink.models import Image
from remote_eink.storage.images import ImageStore, ListenableImageStore, ImageStoreEvent

DEFAULT_SECONDS_BETWEEN_CYCLE = float(60 * 60)


class ImageNotFoundError(ValueError):
    """
    Raised when an image cannot be found when expected.
    """
    def __init__(self, image_id: str):
        super().__init__(f"Image cannot be found: {image_id}")


class DisplayController:
    """
    TODO
    """
    @property
    def current_image(self) -> Image:
        return self._current_image

    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_orientation: int = 0):
        """
        TODO
        :param driver:
        :param identifier:
        :param image_store:
        :param image_orientation:
        """
        self.identifier = identifier if identifier is not None else str(uuid4())
        self.driver = ListenableDisplayDriver(driver)
        self._current_image = None
        self.image_store = ListenableImageStore(image_store)
        self.image_orientation = image_orientation

        self.image_store.event_listeners.add_listener(self._on_remove_image, ImageStoreEvent.REMOVE)
        self.driver.event_listeners.add_listener(self._on_clear, DisplayDriverEvent.CLEAR)
        self.driver.event_listeners.add_listener(self._on_display, DisplayDriverEvent.DISPLAY)

    def display(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        image = self.image_store.get(image_id)
        if image is None:
            raise ImageNotFoundError(image_id)
        if image != self.current_image:
            self.driver.display(image)
            # Valid assertion only if event handlers are ran in same thread
            assert self._current_image == image

    def _on_remove_image(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.driver.clear()

    def _on_clear(self):
        assert self.driver.image is None
        self._current_image = None

    def _on_display(self, image: Image):
        assert self.driver.image == image
        if self.image_store.get(image.identifier) is None:
            self.image_store.add(image)
        self._current_image = image


class CyclableDisplayController(DisplayController):
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_orientation: int = 0):
        """
        TODO
        :param driver:
        :param image_store:
        :param identifier:
        :param image_orientation:
        """
        super().__init__(driver, image_store, identifier, image_orientation)
        self._image_queue = []
        self.image_store.event_listeners.add_listener(
            lambda image: self._add_to_queue(image.identifier), ImageStoreEvent.ADD)
        for image in self.image_store.list():
            self._add_to_queue(image.identifier)

    def display_next_image(self) -> Optional[Image]:
        """
        TODO
        :return:
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
        TODO
        :param image_id:
        :return:
        """
        self._image_queue.append(image_id)

    def _on_remove_image(self, image_id: str):
        if self.current_image and self.current_image.identifier == image_id:
            self.display_next_image()


class AutoCyclingDisplayController(CyclableDisplayController):
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, image_store: ImageStore,
                 identifier: Optional[str] = None, image_orientation: int = 0,
                 cycle_image_after_seconds: float = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        TODO
        :param driver:
        :param image_store:
        :param identifier:
        :param image_orientation:
        :param cycle_image_after_seconds:
        """
        super().__init__(driver, image_store, identifier, image_orientation)
        self.cycle_image_after_seconds = cycle_image_after_seconds
        self._scheduler = BackgroundScheduler()

    def start(self):
        if self._scheduler.state != STATE_RUNNING:
            self._scheduler.start()
            self._scheduler.add_job(self.display_next_image, "interval", seconds=self.cycle_image_after_seconds)

    def stop(self):
        self._scheduler.remove_all_jobs()
        self._scheduler.pause()
