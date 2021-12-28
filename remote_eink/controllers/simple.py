from typing import Optional, Sequence
from uuid import uuid4

from remote_eink.controllers.base import ListenableDisplayController, ImageNotFoundError
from remote_eink.drivers.base import ListenableDisplayDriver, DisplayDriver
from remote_eink.events import EventListenerController
from remote_eink.images import Image
from remote_eink.storage.image.base import ListenableImageStore, ImageStore
from remote_eink.transformers import ImageTransformerSequence, ImageTransformer
from remote_eink.transformers.sequence import SimpleImageTransformerSequence


class SimpleDisplayController(ListenableDisplayController):
    """
    Simple display controller.
    """

    @property
    def friendly_type_name(self) -> str:
        return "Simple"

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def current_image(self) -> Optional[Image]:
        # The reason why we don't return `self._driver.image` is that the device may be displaying a transformation of
        # the image
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

    @property
    def event_listeners(self) -> EventListenerController[ListenableDisplayController.Event]:
        return self._event_listeners

    def __init__(
        self,
        driver: DisplayDriver,
        image_store: ImageStore,
        identifier: Optional[str] = None,
        image_transformers: Sequence[ImageTransformer] = (),
    ):
        """
        Constructor.
        :param driver: display driver
        :param image_store: image store
        :param identifier: driver identifier
        :param image_transformers: image display transformers
        """
        self._identifier = identifier if identifier is not None else str(uuid4())
        self._driver = ListenableDisplayDriver(driver)
        self._current_image = None
        self._image_store = ListenableImageStore(image_store)
        self._image_transformers = SimpleImageTransformerSequence(image_transformers)

        self._display_requested = False
        self._event_listeners = EventListenerController[ListenableDisplayController.Event]()
        self._image_store.event_listeners.add_listener(self._on_remove_image, ListenableImageStore.Event.REMOVE)
        self._driver.event_listeners.add_listener(self._on_clear, ListenableDisplayDriver.Event.CLEAR)
        self._driver.event_listeners.add_listener(self._on_display, ListenableDisplayDriver.Event.DISPLAY)

    def display(self, image_id: str):
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

    def clear(self):
        self.driver.clear()

    def apply_image_transforms(self, image: Image) -> Image:
        for transformer in self.image_transformers:
            if transformer.active:
                image = transformer.transform(image)
        return image

    def _on_remove_image(self, image_id: str):
        """
        Handler for when an image has been removed from the image store.
        :param image_id: ID of the image that has been removed
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.driver.clear()

    def _on_clear(self):
        """
        Handler for when the display is cleared via the driver.
        """
        assert self.driver.image is None
        self._current_image = None
        self.event_listeners.call_listeners(ListenableDisplayController.Event.DISPLAY_CHANGE)

    def _on_display(self, image: Image):
        """
        Handler for when an image is displayed via the driver.
        :param image: the image that has been displayed
        """
        assert self.driver.image == image
        if not self._display_requested:
            # Driver has been used directly to update - cope with it
            if self.image_store.get(image.identifier) is None:
                self.image_store.add(image)
            self._current_image = image
        self.event_listeners.call_listeners(ListenableDisplayController.Event.DISPLAY_CHANGE)
