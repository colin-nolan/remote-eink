import os
import shutil
import tempfile
import unittest
from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic

from remote_eink.storage.manifests import Manifest, InMemoryManifest, ManifestRecord, TinyDbManifest
from remote_eink.tests.storage._common import EXAMPLE_IMAGE_1, EXAMPLE_IMAGE_2

_EXAMPLE_MANIFEST_RECORD_1 = ManifestRecord(EXAMPLE_IMAGE_1.identifier, EXAMPLE_IMAGE_1.type, "test/1.png")
_EXAMPLE_MANIFEST_RECORD_2 = ManifestRecord(EXAMPLE_IMAGE_2.identifier, EXAMPLE_IMAGE_2.type, "2.png")

_ManifestType = TypeVar("_ManifestType", bound=Manifest)


class _TestManifest(unittest.TestCase, Generic[_ManifestType], metaclass=ABCMeta):
    """
    Tests for `Manifest` implementations.
    """
    @abstractmethod
    def create_manifest(self, *args, **kwargs) -> _ManifestType:
        """
        Manifest test.
        :param args: optional args to consider during the creation
        :param kwargs: optional kwargs to consider during the creation
        :return: the manifest
        """

    def setUp(self):
        super().setUp()
        self.manifest = self.create_manifest()

    def test_get_by_id(self):
        self._add_record(_EXAMPLE_MANIFEST_RECORD_1)
        self.assertEqual(_EXAMPLE_MANIFEST_RECORD_1,
                         self.manifest.get_by_image_id(_EXAMPLE_MANIFEST_RECORD_1.identifier))

    def test_get_by_id_when_does_not_exist(self):
        self.assertIsNone(self.manifest.get_by_image_id("does-not-exist"))

    def test_get_by_storage_location(self):
        self._add_record(_EXAMPLE_MANIFEST_RECORD_1)
        self.assertEqual(_EXAMPLE_MANIFEST_RECORD_1, self.manifest.get_by_storage_location(
            _EXAMPLE_MANIFEST_RECORD_1.storage_location))

    def test_get_by_storage_location_when_does_not_exist(self):
        self.assertIsNone(self.manifest.get_by_storage_location("does-not-exist"))

    def test_add(self):
        self._add_record(_EXAMPLE_MANIFEST_RECORD_1)
        self._add_record(_EXAMPLE_MANIFEST_RECORD_2)
        self.assertEqual(
            _EXAMPLE_MANIFEST_RECORD_1, self.manifest.get_by_image_id(_EXAMPLE_MANIFEST_RECORD_1.identifier))
        self.assertEqual(
            _EXAMPLE_MANIFEST_RECORD_2, self.manifest.get_by_image_id(_EXAMPLE_MANIFEST_RECORD_2.identifier))

    def test_add_with_same_identifier(self):
        self._add_record(_EXAMPLE_MANIFEST_RECORD_1)
        self._add_record(_EXAMPLE_MANIFEST_RECORD_2)
        self.assertEqual(
            _EXAMPLE_MANIFEST_RECORD_1, self.manifest.get_by_image_id(_EXAMPLE_MANIFEST_RECORD_1.identifier))

    def test_remove(self):
        self._add_record(_EXAMPLE_MANIFEST_RECORD_1)
        self._add_record(_EXAMPLE_MANIFEST_RECORD_2)
        self.assertTrue(self.manifest.remove(_EXAMPLE_MANIFEST_RECORD_1.identifier))
        self.assertCountEqual([_EXAMPLE_MANIFEST_RECORD_2], self.manifest.list())
        self.assertTrue(self.manifest.remove(_EXAMPLE_MANIFEST_RECORD_2.identifier))
        self.assertCountEqual([], self.manifest.list())

    def test_remove_non_existent(self):
        self.assertFalse(self.manifest.remove("does-not-exist"))

    def _add_record(self, record: ManifestRecord):
        assert isinstance(record, ManifestRecord)
        self.manifest.add(record.identifier, record.image_type, record.storage_location)


class TestInMemoryManifest(_TestManifest[InMemoryManifest]):
    """
    Tests `InMemoryManifest`.
    """
    def create_manifest(self, *args, **kwargs) -> InMemoryManifest:
        return InMemoryManifest()


class TestTinyDbManifest(_TestManifest[TinyDbManifest]):
    """
    Tests `TinyDbManifest`.
    """
    def setUp(self):
        self._temp_directories = []
        super().setUp()

    def tearDown(self):
        super().tearDown()
        while len(self._temp_directories) > 0:
            directory = self._temp_directories.pop()
            shutil.rmtree(directory, ignore_errors=True)

    def create_manifest(self, *args, **kwargs) -> TinyDbManifest:
        temp_directory = tempfile.mkdtemp()
        self._temp_directories.append(temp_directory)
        manifest = TinyDbManifest(os.path.join(temp_directory, "database.db"))
        return manifest

    def test_re_open_manifest(self):
        self.manifest.add(_EXAMPLE_MANIFEST_RECORD_1.identifier, _EXAMPLE_MANIFEST_RECORD_1.image_type,
                          _EXAMPLE_MANIFEST_RECORD_1.storage_location)
        manifest = TinyDbManifest(self.manifest.database_location)
        self.assertEqual(_EXAMPLE_MANIFEST_RECORD_1, manifest.get_by_image_id(_EXAMPLE_MANIFEST_RECORD_1.identifier))


del _TestManifest

if __name__ == "__main__":
    unittest.main()
