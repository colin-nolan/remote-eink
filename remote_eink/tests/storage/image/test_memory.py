import unittest

from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE
from remote_eink.tests.storage.image._common import AbstractTest


class TestInMemoryImageStore(AbstractTest.TestImageStore[InMemoryImageStore]):
    """
    Tests `InMemoryImageStore`.
    """

    def create_image_store(self, *args, **kwargs) -> InMemoryImageStore:
        return InMemoryImageStore(*args, **kwargs)

    def test_init_with_images(self):
        image_store = self.create_image_store([WHITE_IMAGE, BLACK_IMAGE])
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), image_store.list())


if __name__ == "__main__":
    unittest.main()
