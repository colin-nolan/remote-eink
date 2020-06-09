import logging
from io import BytesIO

from remote_eink.drivers.base import BaseDisplayDriver

logger = logging.getLogger(__name__)

try:
    from papertty.drivers.drivers_base import DisplayDriver as DeviceDisplayDriver
    from papertty.papertty import PaperTTY, display_image
    from PIL import Image as PILImage
except ImportError:
    logger.error("\"papertty\" extra not installed")
    raise


class PaperTtyDisplayDriver(BaseDisplayDriver):
    """
    PaperTTY-based device driver.
    """
    def __init__(self, device_driver: DeviceDisplayDriver):
        """
        Constructor.
        :param device_driver: PaperTTY device display driver
        """
        super().__init__()
        self._device_driver = device_driver
        self._papertty: PaperTTY = None

    def _display(self, image_data: bytes):
        display_image(self._device_driver, PILImage.open(BytesIO(image_data)))

    def _clear(self):
        self._papertty.clear()

    def _sleep(self):
        self._papertty.sleep()
        self._papertty = None

    def _wake(self):
        if self._papertty is not None:
            self._papertty = PaperTTY(self._device_driver)
            self._papertty.init_display()
