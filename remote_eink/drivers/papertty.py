import logging
from io import BytesIO
from typing import Callable, TypeVar, ParamSpec

from remote_eink.drivers.base import BaseDisplayDriver

logger = logging.getLogger(__name__)

try:
    from papertty.drivers.drivers_base import DisplayDriver as DeviceDisplayDriver
    from papertty.papertty import PaperTTY, display_image
    from PIL import Image as PILImage
except ImportError:
    logger.error('"papertty" extra not installed')
    raise

_P = ParamSpec("_P")
_T = TypeVar("_T")


def _assert_papertty_instantiated(to_wrap: Callable[_P, _T]) -> Callable[_P, _T]:
    def wrapper(self, *args, **kwargs) -> _T:
        if self._papertty is None:
            raise AssertionError("PaperTTY is not instantiated")
        return to_wrap(*args, **kwargs)

    return wrapper


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
        # self._papertty: Optional[PaperTTY] = None
        # Wake will initialise PaperTTY
        self._wake()

    @_assert_papertty_instantiated
    def _display(self, image_data: bytes):
        display_image(self._papertty.driver, PILImage.open(BytesIO(image_data)))

    @_assert_papertty_instantiated
    def _clear(self):
        self._papertty.clear()

    @_assert_papertty_instantiated
    def _sleep(self):
        # XXX: `sleep` is not part of the `BaseDisplayDriver` superclass but it is defined on all the subclasses
        self._papertty.sleep()
        self._papertty = None

    def _wake(self):
        if self._papertty is None:
            self._papertty = PaperTTY(self._device_driver.__name__)
            self._papertty.init_display()
