import io
from typing import Type

import logging
from io import BytesIO

from remote_eink.drivers.base import BaseDisplayDriver

logger = logging.getLogger(__name__)

try:
    from PIL import Image as PILImage, Image
except ImportError:
    # TODO
    logger.error("\"TODO\" extra not installed")
    raise


class LocalDisplayDriver(BaseDisplayDriver):
    """
    Local display device driver.
    """

    def __init__(self):
        super().__init__()
        self._image = None

    def _display(self, image_data: bytes):
        image = Image.open(io.BytesIO(image_data))
        image.show()

    def _clear(self):
        pass

    def _sleep(self):
        pass

    def _wake(self):
        pass

