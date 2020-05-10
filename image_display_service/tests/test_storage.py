import unittest
from abc import abstractmethod, ABCMeta
from io import BytesIO
from typing import TypeVar, Generic

from image_display_service.image import Image
from image_display_service.storage import ImageStore, InMemoryImageStore

EXAMPLE_IMAGE_1 = Image("example-1", lambda: b"abc")
EXAMPLE_IMAGE_2 = Image("example-2", lambda: b"def")

_ImageStoreType = TypeVar("_ImageStoreType", bound=ImageStore)


class _TestImageStore(unittest.TestCase, Generic[_ImageStoreType], metaclass=ABCMeta):
    """
    Tests for `ImageStore` implementations.
    """
    def setUp(self):
        self.image_store = self.create_image_store()

    def test_init_with_images(self):
        image_store = self.create_image_store([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), image_store.list())

    def test_retrieve_non_existent(self):
        self.assertIsNone(self.image_store.retrieve("does-not-exist"))

    def test_list(self):
        self.image_store.save(EXAMPLE_IMAGE_1)
        self.image_store.save(EXAMPLE_IMAGE_2)
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), self.image_store.list())

    def test_save(self):
        self.image_store.save(EXAMPLE_IMAGE_1)
        self.image_store.save(EXAMPLE_IMAGE_2)
        self.assertEqual(EXAMPLE_IMAGE_1, self.image_store.retrieve(EXAMPLE_IMAGE_1.identifier))
        self.assertEqual(EXAMPLE_IMAGE_2, self.image_store.retrieve(EXAMPLE_IMAGE_2.identifier))

    def test_save_with_same_identifier(self):
        self.image_store.save(EXAMPLE_IMAGE_1)
        self.assertRaises(ValueError, self.image_store.save, EXAMPLE_IMAGE_1)

    def test_delete(self):
        self.image_store.save(EXAMPLE_IMAGE_1)
        self.image_store.save(EXAMPLE_IMAGE_2)
        self.assertTrue(self.image_store.delete(EXAMPLE_IMAGE_1.identifier))
        self.assertCountEqual([EXAMPLE_IMAGE_2], self.image_store.list())
        self.assertTrue(self.image_store.delete(EXAMPLE_IMAGE_2.identifier))
        self.assertCountEqual([], self.image_store.list())

    def test_delete_non_existent(self):
        self.assertFalse(self.image_store.delete("does-not-exist"))

    @abstractmethod
    def create_image_store(self, *args, **kwargs) -> _ImageStoreType:
        """
        Image store to test.
        :param args: optional args to consider during the creation
        :param kwargs: optional kwargs to consider during the creation
        :return: the image store
        """


class TestInMemoryImageStore(_TestImageStore[InMemoryImageStore]):
    """
    Tests `InMemoryImageStore`.
    """
    def create_image_store(self, *args, **kwargs) -> InMemoryImageStore:
        return InMemoryImageStore(*args, **kwargs)


del _TestImageStore

if __name__ == "__main__":
    unittest.main()
