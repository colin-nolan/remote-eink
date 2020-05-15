from typing import Optional, List
from uuid import uuid4

from remote_eink.display.drivers import DisplayDriver
from remote_eink.models import Image
from remote_eink.storage.images import ImageStore

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
    def current_image(self) -> Image:
        return self._current_image

    @property
    def sleeping(self) -> bool:
        return self._driver.sleeping

    def __init__(self, driver: DisplayDriver, identifier: Optional[str] = None,
                 image_store: Optional[ImageStore] = None, image_orientation: int = 0, cycle_images: bool = True,
                 cycle_randomly: bool = False, cycle_image_after_seconds: int = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        TODO
        :param driver:
        :param identifier:
        :param image_store:
        :param image_orientation:
        :param cycle_images:
        :param cycle_randomly:
        :param cycle_image_after_seconds:
        """
        self.identifier = identifier if identifier is not None else str(uuid4())
        self._driver = driver
        self._current_image = None
        self._image_store = image_store
        self.image_orientation = image_orientation
        self.cycle_images = cycle_images
        self.cycle_images_randomly = cycle_randomly
        self.cycle_image_after_seconds = cycle_image_after_seconds

    # FIXME
    def display(self, image_id: str):
        """
        TODO
        :param image_id:
        :return:
        """
        image = self._image_store.get(image_id)
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

    def get_image(self, image_id: str) -> Optional[Image]:
        """
        TODO
        :param image_id:
        :return:
        """
        return self._image_store.get(image_id)

    def list_images(self) -> List[Image]:
        """
        TODO
        :return:
        """
        return self._image_store.list()

    def add_image(self, image: Image):
        """
        TODO
        :param image:
        :return:
        """
        return self._image_store.add(image)

    def remove_image(self, image_id: str) -> bool:
        """
        TODO
        :param image_id:
        :return:
        """
        removed = self._image_store.remove(image_id)
        if self.current_image and self.current_image.identifier == image_id:
            self.next_image()
        return removed

    def next_image(self) -> Image:
        """
        TODO
        :return:
        """
        # FIXME