import unittest
from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic

from remote_eink.images import FunctionBasedImage
from remote_eink.storage.image.base import (
    ImageStore,
    ImageAlreadyExistsError,
)
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE

_ImageStoreType = TypeVar("_ImageStoreType", bound=ImageStore)


class AbstractTest:
    class TestImageStore(unittest.TestCase, Generic[_ImageStoreType], metaclass=ABCMeta):
        """
        Tests for `ImageStore` implementations.
        """

        @abstractmethod
        def create_image_store(self, *args, **kwargs) -> _ImageStoreType:
            """
            Image store to test.
            :param args: optional args to consider during the creation
            :param kwargs: optional kwargs to consider during the creation
            :return: the image store
            """

        def setUp(self):
            super().setUp()
            self.image_store: _ImageStoreType = self.create_image_store()

        def test_len(self):
            self.image_store.add(BLACK_IMAGE)
            self.assertEqual(1, len(self.image_store))

        def test_iter(self):
            images = (BLACK_IMAGE, WHITE_IMAGE)
            for image in images:
                self.image_store.add(image)
            self.assertCountEqual(images, self.image_store)

        def test_contains(self):
            self.image_store.add(BLACK_IMAGE)
            self.assertIn(BLACK_IMAGE, self.image_store)
            self.assertNotIn(WHITE_IMAGE, self.image_store)

        def test_get_non_existent(self):
            self.assertIsNone(self.image_store.get("does-not-exist"))

        def test_list(self):
            self.image_store.add(WHITE_IMAGE)
            self.image_store.add(BLACK_IMAGE)
            self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), self.image_store.list())

        def test_set(self):
            self.image_store.add(WHITE_IMAGE)
            self.image_store.add(BLACK_IMAGE)
            self.assertEqual(WHITE_IMAGE, self.image_store.get(WHITE_IMAGE.identifier))
            self.assertEqual(BLACK_IMAGE, self.image_store.get(BLACK_IMAGE.identifier))

        def test_set_with_same_identifier(self):
            self.image_store.add(WHITE_IMAGE)
            self.assertRaises(ImageAlreadyExistsError, self.image_store.add, WHITE_IMAGE)

        def test_set_with_same_image_data(self):
            self.image_store.add(WHITE_IMAGE)
            white_image_copy = FunctionBasedImage(BLACK_IMAGE.identifier, lambda: WHITE_IMAGE.data, WHITE_IMAGE.type)
            self.image_store.add(white_image_copy)
            self.assertEqual(WHITE_IMAGE, self.image_store.get(WHITE_IMAGE.identifier))
            self.assertEqual(white_image_copy, self.image_store.get(white_image_copy.identifier))

        def test_remove(self):
            self.image_store.add(WHITE_IMAGE)
            self.image_store.add(BLACK_IMAGE)
            self.assertTrue(self.image_store.remove(WHITE_IMAGE.identifier))
            self.assertCountEqual([BLACK_IMAGE], self.image_store.list())
            self.assertTrue(self.image_store.remove(BLACK_IMAGE.identifier))
            self.assertCountEqual([], self.image_store.list())

        def test_remove_non_existent(self):
            self.assertFalse(self.image_store.remove("does-not-exist"))
