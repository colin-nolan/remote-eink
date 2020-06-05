import shutil
import tempfile
import unittest
from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic

from remote_eink.images import Image
from remote_eink.storage.images import ImageStore, InMemoryImageStore, ImageAlreadyExistsError, FileSystemImageStore, \
    ListenableImageStore, ProxyImageStore
from remote_eink.tests._common import TestProxy
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE

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
        image_1_copy = Image(BLACK_IMAGE.identifier, lambda: WHITE_IMAGE.data, WHITE_IMAGE.type)
        self.image_store.add(image_1_copy)
        self.assertEqual(WHITE_IMAGE, self.image_store.get(WHITE_IMAGE.identifier))
        self.assertEqual(image_1_copy, self.image_store.get(image_1_copy.identifier))

    def test_remove(self):
        self.image_store.add(WHITE_IMAGE)
        self.image_store.add(BLACK_IMAGE)
        self.assertTrue(self.image_store.remove(WHITE_IMAGE.identifier))
        self.assertCountEqual([BLACK_IMAGE], self.image_store.list())
        self.assertTrue(self.image_store.remove(BLACK_IMAGE.identifier))
        self.assertCountEqual([], self.image_store.list())

    def test_remove_non_existent(self):
        self.assertFalse(self.image_store.remove("does-not-exist"))


class TestInMemoryImageStore(_TestImageStore[InMemoryImageStore]):
    """
    Tests `InMemoryImageStore`.
    """
    def test_init_with_images(self):
        image_store = self.create_image_store([WHITE_IMAGE, BLACK_IMAGE])
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), image_store.list())

    def create_image_store(self, *args, **kwargs) -> InMemoryImageStore:
        return InMemoryImageStore(*args, **kwargs)


class TestFileSystemImageStore(_TestImageStore[InMemoryImageStore]):
    """
    Tests `FileSystemImageStore`.
    """
    def test_init_with_images(self):
        image_store = self.create_image_store([WHITE_IMAGE, BLACK_IMAGE])
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), image_store.list())

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

        self.image_store.event_listeners.add_listener(add_listener, ListenableImageStore.Event.ADD)
        self.image_store.add(WHITE_IMAGE)
        self.assertEqual(added, WHITE_IMAGE)

    def test_remove_listener(self):
        removed = None

        def remove_listener(image_id):
            nonlocal removed
            removed = image_id

        self.image_store.event_listeners.add_listener(remove_listener, ListenableImageStore.Event.REMOVE)
        self.image_store.remove(WHITE_IMAGE.identifier)
        self.assertEqual(removed, WHITE_IMAGE.identifier)

    def create_image_store(self, *args, **kwargs) -> ListenableImageStore:
        return ListenableImageStore(InMemoryImageStore(*args, **kwargs))


class TestProxyImageStore(_TestImageStore[ProxyImageStore], TestProxy):
    """
    Test for `ProxyImageStore`.
    """
    def create_image_store(self, *args, **kwargs) -> ProxyImageStore:
        receiver = self.setup_receiver(InMemoryImageStore(*args, **kwargs))
        return ProxyImageStore(receiver.connector)


del _TestImageStore

if __name__ == "__main__":
    unittest.main()
