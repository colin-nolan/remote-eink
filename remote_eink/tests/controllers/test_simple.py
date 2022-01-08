import unittest
from typing import Optional

from remote_eink.controllers.simple import SimpleDisplayController
from remote_eink.storage.image.base import ImageStore
from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.controllers._common import AbstractTest
from remote_eink.tests.drivers._common import DummyBaseDisplayDriver


class TestSimpleDisplayController(AbstractTest.TestDisplayController[SimpleDisplayController]):
    """
    Test for `SimpleDisplayController`.
    """

    def create_display_controller(
        self, image_store: Optional[ImageStore] = None, *args, **kwargs
    ) -> SimpleDisplayController:
        return SimpleDisplayController(
            DummyBaseDisplayDriver(), image_store if image_store is not None else InMemoryImageStore()
        )


# TODO: test `SleepyDisplayController`


if __name__ == "__main__":
    unittest.main()
