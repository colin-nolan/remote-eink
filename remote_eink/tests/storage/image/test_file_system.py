import os
import shutil
import tempfile
import unittest

from remote_eink.storage.image.file_system import FileSystemImageStore
from remote_eink.storage.image.memory import InMemoryImageStore
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE
from remote_eink.tests.storage.image._common import AbstractTest


class TestFileSystemImageStore(AbstractTest.TestImageStore[InMemoryImageStore]):
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

    def test_when_directory_not_exist(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            storage_directory = f"{temp_directory}/does/not/exist"
            assert not os.path.exists(storage_directory)
            store = FileSystemImageStore(storage_directory)
            store.list()
            self.assertTrue(os.path.exists(storage_directory))


if __name__ == "__main__":
    unittest.main()
