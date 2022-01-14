import os
import shutil
import tempfile
import unittest
from typing import TypeVar

from remote_eink.storage.image.base import (
    ImageStore,
    ListenableImageStore,
)
from remote_eink.storage.image.file_system import FileSystemImageStore
from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE
from remote_eink.tests.storage.image._common import AbstractTest

_ImageStoreType = TypeVar("_ImageStoreType", bound=ImageStore)


class TestFileSystemImageStore(AbstractTest.TestImageStore[InMemoryImageStore]):
    """
    Tests `FileSystemImageStore`.
    """

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

    def test_init_with_images(self):
        image_store = self.create_image_store([WHITE_IMAGE, BLACK_IMAGE])
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), image_store.list())

    def test_when_directory_not_exist(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            storage_directory = f"{temp_directory}/does/not/exist"
            assert not os.path.exists(storage_directory)
            store = FileSystemImageStore(storage_directory)
            store.list()
            self.assertTrue(os.path.exists(storage_directory))


class TestListenableImageStore(AbstractTest.TestImageStore[ListenableImageStore]):
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


if __name__ == "__main__":
    unittest.main()
