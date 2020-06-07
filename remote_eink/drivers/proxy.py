from typing import Optional

from remote_eink.drivers.base import DisplayDriver
from remote_eink.images import Image, ReallySimpleImage
from remote_eink.multiprocess import ProxyObject


class ProxyDisplayDriver(DisplayDriver, ProxyObject):
    """
    TODO
    """
    @property
    def sleeping(self) -> bool:
        return self._communicate("sleeping")

    @property
    def image(self) -> Optional[Image]:
        return self._communicate("image")

    def display(self, image: Image):
        image = ReallySimpleImage(image.identifier, image.data, image.type)
        self._communicate("display", image)

    def clear(self):
        self._communicate("clear")

    def sleep(self):
        self._communicate("sleep")

    def wake(self):
        self._communicate("wake")
