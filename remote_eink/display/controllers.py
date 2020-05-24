from typing import Optional, Sequence
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

from remote_eink.display.drivers import DisplayDriver, ListenableDisplayDriver, DisplayDriverEvent
from remote_eink.transformers.transformers import ImageTransformer, ImageTransformerSequence
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
    Display controller.
    """
    @property
    def current_image(self) -> Image:
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

    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_transformers: Sequence[ImageTransformer] = ()):
        """
        Constructor.
        :param driver: display driver
        :param image_store: image store
        :param identifier: driver identifier
        :param image_transformers: image display transformers
        """
        self.identifier = identifier if identifier is not None else str(uuid4())
        self._driver = ListenableDisplayDriver(driver)
        self._current_image = None
        self._image_store = ListenableImageStore(image_store)
        self._image_transformers = ImageTransformerSequence(image_transformers)
        self._display_requested = False

        self._image_store.event_listeners.add_listener(self._on_remove_image, ImageStoreEvent.REMOVE)
        self._driver.event_listeners.add_listener(self._on_clear, DisplayDriverEvent.CLEAR)
        self._driver.event_listeners.add_listener(self._on_display, DisplayDriverEvent.DISPLAY)

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
            transformed_image = self.apply_image_transforms(image)
            self._display_requested = True
            try:
                self.driver.display(transformed_image)
            finally:
                self._display_requested = False
            self._current_image = image

    def apply_image_transforms(self, image: Image) -> Image:
        """
        TODO
        :param image:
        :return:
        """
        # TODO: sort transformers some way as order matters?
        for transformer in self.image_transformers:
            if transformer.active:
                image = transformer.transform(image)
        return image

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
        if not self._display_requested:
            # Driver has been used directly to update - cope with it
            if self.image_store.get(image.identifier) is None:
                self.image_store.add(image)
            self._current_image = image


class CyclableDisplayController(DisplayController):
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, image_store: ImageStore, identifier: Optional[str] = None,
                 image_transformers: Sequence[ImageTransformer] = ()):
        """
        TODO
        :param driver:
        :param image_store:
        :param identifier:
        :param image_transformers:
        """
        super().__init__(driver, image_store, identifier, image_transformers)
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
                 identifier: Optional[str] = None, image_transformers: Sequence[ImageTransformer] = (),
                 cycle_image_after_seconds: float = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        TODO
        :param driver:
        :param image_store:
        :param identifier:
        :param image_transformers:
        :param cycle_image_after_seconds:
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
        self._scheduler.pause()
