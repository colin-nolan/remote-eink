from typing import Optional
from uuid import uuid4

from image_display_service.display.drivers import DisplayDriver, Image

DEFAULT_SECONDS_BETWEEN_ROTATE = 60 * 60


class DisplayController:
    """
    TODO
    """
    def __init__(self, driver: DisplayDriver, identifier: Optional[str] = None, rotate_images: bool = True,
                 random_rotate: bool = False, seconds_between_rotate: int = DEFAULT_SECONDS_BETWEEN_ROTATE):
        """
        TODO
        :param driver:
        :param rotate_images:
        :param random_rotate:
        :param seconds_between_rotate:
        """
        self.identifier = identifier if identifier is not None else str(uuid4())
        self.driver = driver
        self.rotate_images = rotate_images
        self.random_rotate = random_rotate
        self.seconds_between_rotate = seconds_between_rotate

    def display(self, image: Image):
        self.driver.display(image)

    def clear(self):
        self.driver.clear()

    def sleep(self):
        self.driver.sleep()