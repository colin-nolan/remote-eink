import shutil
import tempfile
import unittest
from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic

from remote_eink.models import Image
from remote_eink.storage.images import ImageStore, InMemoryImageStore, ImageAlreadyExistsError, FileSystemImageStore, \
    ListenableImageStore, ImageStoreEvent
from remote_eink.tests.storage._common import EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2

_ImageStoreType = TypeVar("_ImageStoreType", bound=ImageStore)


class _TestImageStore(unittest.TestCase, Generic[_ImageStoreType], metaclass=ABCMeta):
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

    def test_get_non_existent(self):
        self.assertIsNone(self.image_store.get("does-not-exist"))

    def test_list(self):
        self.image_store.add(EXAMPLE_IMAGE_1)
        self.image_store.add(EXAMPLE_IMAGE_2)
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), self.image_store.list())

    def test_set(self):
        self.image_store.add(EXAMPLE_IMAGE_1)
        self.image_store.add(EXAMPLE_IMAGE_2)
        self.assertEqual(EXAMPLE_IMAGE_1, self.image_store.get(EXAMPLE_IMAGE_1.identifier))
        self.assertEqual(EXAMPLE_IMAGE_2, self.image_store.get(EXAMPLE_IMAGE_2.identifier))

    def test_set_with_same_identifier(self):
        self.image_store.add(EXAMPLE_IMAGE_1)
        self.assertRaises(ImageAlreadyExistsError, self.image_store.add, EXAMPLE_IMAGE_1)

    def test_set_with_same_image_data(self):
        self.image_store.add(EXAMPLE_IMAGE_1)
        image_1_copy = Image(EXAMPLE_IMAGE_2.identifier, lambda: EXAMPLE_IMAGE_1.data, EXAMPLE_IMAGE_1.type)
        self.image_store.add(image_1_copy)
        self.assertEqual(EXAMPLE_IMAGE_1, self.image_store.get(EXAMPLE_IMAGE_1.identifier))
        self.assertEqual(image_1_copy, self.image_store.get(image_1_copy.identifier))

    def test_remove(self):
        self.image_store.add(EXAMPLE_IMAGE_1)
        self.image_store.add(EXAMPLE_IMAGE_2)
        self.assertTrue(self.image_store.remove(EXAMPLE_IMAGE_1.identifier))
        self.assertCountEqual([EXAMPLE_IMAGE_2], self.image_store.list())
        self.assertTrue(self.image_store.remove(EXAMPLE_IMAGE_2.identifier))
        self.assertCountEqual([], self.image_store.list())

    def test_remove_non_existent(self):
        self.assertFalse(self.image_store.remove("does-not-exist"))


class TestInMemoryImageStore(_TestImageStore[InMemoryImageStore]):
    """
    Tests `InMemoryImageStore`.
    """
    def test_init_with_images(self):
        image_store = self.create_image_store([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), image_store.list())

    def create_image_store(self, *args, **kwargs) -> InMemoryImageStore:
        return InMemoryImageStore(*args, **kwargs)


class TestFileSystemImageStore(_TestImageStore[InMemoryImageStore]):
    """
    Tests `FileSystemImageStore`.
    """
    def test_init_with_images(self):
        image_store = self.create_image_store([EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2])
        self.assertCountEqual((EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2), image_store.list())

    def setUp(self):
        self._temp_directories = []
        super().setUp()

    def tearDown(self):
        super().tearDown()
        while len(self._temp_directories) > 0:
            directory = self._temp_directories.pop()
            shutil.rmtree(directory, ignore_errors=True)

    def create_image_store(self, *args, **kwargs) -> FileSystemImageStore:
        temp_directory = tempfile.mkdtemp()
        self._temp_directories.append(temp_directory)
        return FileSystemImageStore(temp_directory, *args, **kwargs)


class TestListenableImageStore(_TestImageStore[ListenableImageStore]):
    """
    Tests `ListenableImageStore`.
    """
    def test_add_listener(self):
        added = None

        def add_listener(image):
            nonlocal added
            added = image

        self.image_store.event_listeners.add_listener(add_listener, ImageStoreEvent.ADD)
        self.image_store.add(EXAMPLE_IMAGE_1)
        self.assertEqual(added, EXAMPLE_IMAGE_1)

    def test_remove_listener(self):
        removed = None

        def remove_listener(image_id):
            nonlocal removed
            removed = image_id

        self.image_store.event_listeners.add_listener(remove_listener, ImageStoreEvent.REMOVE)
        self.image_store.remove(EXAMPLE_IMAGE_1.identifier)
        self.assertEqual(removed, EXAMPLE_IMAGE_1.identifier)

    def create_image_store(self, *args, **kwargs) -> ListenableImageStore:
        inner_image_store = InMemoryImageStore()
        return ListenableImageStore(inner_image_store)


del _TestImageStore

if __name__ == "__main__":
    unittest.main()
