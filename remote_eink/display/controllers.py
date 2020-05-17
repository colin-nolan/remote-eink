from typing import Optional
from uuid import uuid4

from remote_eink.display.drivers import DisplayDriver
from remote_eink.models import Image
from remote_eink.storage.images import ImageStore, ListenableImageStore, ImageStoreEvent

DEFAULT_SECONDS_BETWEEN_CYCLE = 60 * 60


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
    def sleeping(self) -> bool:
        return self._driver.sleeping

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
        self._driver = driver
        self._current_image = None
        self.image_store = ListenableImageStore(image_store)
        self.image_orientation = image_orientation

        self.image_store.add_event_listener(lambda image_id: self._on_remove_image(image_id), ImageStoreEvent.REMOVE)

    def display(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        image = self.image_store.get(image_id)
        if image is None:
            raise ImageNotFoundError(image_id)
        self._driver.display(image)
        self._current_image = image

    def clear(self):
        """
        TODO
        :return:
        """
        self._driver.clear()
        self._current_image = None

    def sleep(self):
        """
        TODO
        :return:
        """
        self._driver.sleep()

    def wake(self):
        """
        TODO
        :return:
        """
        self._driver.wake()

    def _on_remove_image(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.clear()


class CyclingDisplayController(DisplayController):
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, image_store: Optional[ImageStore],
                 identifier: Optional[str] = None, image_orientation: int = 0,
                 cycle_images: bool = True, cycle_image_after_seconds: int = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        TODO
        :param driver:
        :param image_store:
        :param identifier:
        :param image_orientation:
        :param cycle_images:
        :param cycle_image_after_seconds:
        """
        super().__init__(driver, image_store, identifier, image_orientation)
        self.cycle_images = cycle_images
        self.cycle_image_after_seconds = cycle_image_after_seconds
        self._image_queue = []
        self.image_store.add_event_listener(lambda image: self._add_to_queue(image.identifier), ImageStoreEvent.ADD)
        for image in self.image_store.list():
            self._add_to_queue(image.identifier)

    def display_next_image(self) -> Optional[Image]:
        """
        TODO
        :return:
        """
        if len(self._image_queue) == 0:
            self.clear()
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
