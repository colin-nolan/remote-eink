from typing import Optional, Sequence

from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

from remote_eink.controllers.simple import SimpleDisplayController
from remote_eink.drivers.base import DisplayDriver
from remote_eink.images import Image
from remote_eink.storage.image.base import ImageStore, ListenableImageStore
from remote_eink.transformers import ImageTransformer, DEFAULT_TRANSFORMERS


class CyclableDisplayController(SimpleDisplayController):
    """
    Display controller that can cycle through the image that it displays.
    """

    @property
    def friendly_type_name(self) -> str:
        return "Cyclable"

    def __init__(
        self,
        driver: DisplayDriver,
        image_store: ImageStore,
        identifier: Optional[str] = None,
        image_transformers: Sequence[ImageTransformer] = DEFAULT_TRANSFORMERS,
    ):
        """
        Constructor.
        :param driver: `BaseDisplayController.__init__`
        :param image_store: `BaseDisplayController.__init__`
        :param identifier: `BaseDisplayController.__init__`
        :param image_transformers: `BaseDisplayController.__init__`
        """
        super().__init__(driver, image_store, identifier, image_transformers)
        self._image_queue = []
        # Note: the superclass converts the image store to a `ListenableImageStore`
        self.image_store.event_listeners.add_listener(
            lambda image: self._add_to_queue(image.identifier), ListenableImageStore.Event.ADD
        )
        for image in self.image_store.list():
            self._add_to_queue(image.identifier)

    def display_next_image(self) -> Optional[Image]:
        """
        Displays the next image in the image queue.
        :return: image displayed or `None` if no images to display
        """
        if len(self._image_queue) == 0:
            self.driver.clear()
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
        Adds the image with the given ID to the queue.
        :param image_id: ID of the image to add to the queue
        """
        self._image_queue.append(image_id)

    def _on_remove_image(self, image_id: str):
        """
        Called when the image with the given ID is removed.
        :param image_id: ID of the image that was removed
        """
        if self.current_image and self.current_image.identifier == image_id:
            self.display_next_image()


class AutoCyclingDisplayController(CyclableDisplayController):
    """
    Display controller that auto cycles through images.
    """

    DEFAULT_SECONDS_BETWEEN_CYCLE = float(60 * 60)

    @property
    def friendly_type_name(self) -> str:
        return "AutoCycling"

    def __init__(
        self,
        driver: DisplayDriver,
        image_store: ImageStore,
        identifier: Optional[str] = None,
        image_transformers: Sequence[ImageTransformer] = DEFAULT_TRANSFORMERS,
        cycle_image_after_seconds: float = DEFAULT_SECONDS_BETWEEN_CYCLE,
    ):
        """
        Constructor.
        :param driver: see `CyclableDisplayController.__init__`
        :param image_store: see `CyclableDisplayController.__init__`
        :param identifier: see `CyclableDisplayController.__init__`
        :param image_transformers: see `CyclableDisplayController.__init__`
        :param cycle_image_after_seconds: the number of seconds before cycling on to the next image
        """
        super().__init__(driver, image_store, identifier, image_transformers)
        self.cycle_image_after_seconds = cycle_image_after_seconds
        self._scheduler = BackgroundScheduler()

    def start(self):
        if self._scheduler.state != STATE_RUNNING:
            self._scheduler.start()
            self._scheduler.add_job(self.display_next_image, "interval", seconds=self.cycle_image_after_seconds)

    def stop(self):
        self._scheduler.remove_all_jobs()
        try:
            self._scheduler.pause()
        except SchedulerNotRunningError:
            pass
