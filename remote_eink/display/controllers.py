from typing import Optional, List
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

    def __init__(self, driver: DisplayDriver, identifier: Optional[str] = None,
                 image_store: Optional[ImageStore] = None, image_orientation: int = 0):
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

    # FIXME
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
    def __init__(self, driver: DisplayDriver, cycle_images: bool = True, cycle_randomly: bool = False,
                 cycle_image_after_seconds: int = DEFAULT_SECONDS_BETWEEN_CYCLE):
        super().__init__(driver)
        self.cycle_images = cycle_images
        self.cycle_images_randomly = cycle_randomly
        self.cycle_image_after_seconds = cycle_image_after_seconds

    def next_image(self) -> Image:
        """
        TODO
        :return:
        """
        # FIXME

    def _on_remove_image(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.next_image()







