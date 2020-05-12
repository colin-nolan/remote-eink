from typing import Optional
from uuid import uuid4

from image_display_service.display.drivers import DisplayDriver
from image_display_service.image import Image
from image_display_service.storage.image_stores import ImageStore

DEFAULT_SECONDS_BETWEEN_CYCLE = 60 * 60


class DisplayController:
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, identifier: Optional[str] = None, current_image: Optional[Image] = None,
                 image_store: Optional[ImageStore] = None, image_orientation: int = 0, cycle_images: bool = True,
                 cycle_randomly: bool = False, cycle_image_after_seconds: int = DEFAULT_SECONDS_BETWEEN_CYCLE):
        """
        TODO
        :param driver:
        :param identifier:
        :param current_image:
        :param image_store:
        :param image_orientation:
        :param cycle_images:
        :param cycle_randomly:
        :param cycle_image_after_seconds:
        """
        self.identifier = identifier if identifier is not None else str(uuid4())
        self.driver = driver
        self.current_image = current_image
        self.image_store = image_store
        self.image_orientation = image_orientation
        self.cycle_images = cycle_images
        self.cycle_images_randomly = cycle_randomly
        self.cycle_image_after_seconds = cycle_image_after_seconds

    def display(self, image: Image):
        """
        TODO
        :param image:
        :return:
        """
        self.driver.display(image)

    def clear(self):
        """
        TODO
        :return:
        """
        self.driver.clear()

    def sleep(self):
        """
        TODO
        :return:
        """
        self.driver.sleep()
