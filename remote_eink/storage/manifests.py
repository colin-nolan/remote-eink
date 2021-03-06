from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField
from tinydb import TinyDB, Query

from remote_eink.images import ImageType


class ManifestAlreadyExistsError(ValueError):
    """
    Raised when an manifest for the image already exists when not allowed.
    """
    def __init__(self, image_id: str):
        super().__init__(f"Manifest for the image already exists: {image_id}")


@dataclass
class ManifestRecord:
    """
    Record in the image storage manifest.
    """
    identifier: str
    image_type: ImageType
    storage_location: str

    def __hash__(self) -> int:
        return hash(self.identifier) + hash(self.storage_location)


class _ManifestRecordSchema(Schema):
    """
    Marshmallow schema for `ManifestRecord`.
    """
    identifier = fields.Str(data_key="id")
    image_type = EnumField(ImageType, data_key="image_type")
    storage_location = fields.Str(data_key="storage_location")

    @post_load
    def make_manifest_record(self, data, **kwargs):
        return ManifestRecord(**data)


class Manifest(metaclass=ABCMeta):
    """
    Image manifest, linking image identifiers to storage information.
    """
    @abstractmethod
    def get_by_image_id(self, image_id: str) -> Optional[ManifestRecord]:
        """
        Gets manifest record for image with the given ID.
        :param image_id: image ID
        :return: manifest record of the image or `None` if no record exists
        """

    @abstractmethod
    def get_by_storage_location(self, storage_location: str) -> Optional[ManifestRecord]:
        """
        Gets manifest record for the image at the given storage location.
        :param storage_location: location image is stored
        :return: manifest record of the image or `None` if no record exists
        """

    @abstractmethod
    def list(self) -> List[ManifestRecord]:
        """
        Lists all the records in the manifest.
        :return: all records
        """

    @abstractmethod
    def add(self, image_id: str, image_type: ImageType, storage_location: str):
        """
        Adds manifest for the image with the given ID, given type that is stored in the given location.
        :param image_id: ID of the image
        :param image_type: type of the image
        :param storage_location: where the image is stored
        """

    @abstractmethod
    def remove(self, image_id: str) -> bool:
        """
        Removes the manifest for the image with the given ID.
        :param image_id: ID of the image
        :return: `True` if an image is removed else `False`
        """


class InMemoryManifest(Manifest):
    """
    In memory manifest implementation.
    """
    def __init__(self):
        """
        Constructor.
        """
        self._manifest_records: Dict[str, ManifestRecord] = {}

    def get_by_image_id(self, image_id: str) -> Optional[ManifestRecord]:
        return self._manifest_records.get(image_id)

    def get_by_storage_location(self, storage_location: str) -> Optional[ManifestRecord]:
        # Not optimising here unless actually required
        try:
            return next(filter(lambda manifest_record: manifest_record.storage_location == storage_location,
                               self._manifest_records.values()))
        except StopIteration:
            return None

    def list(self) -> List[ManifestRecord]:
        return list(self._manifest_records.values())

    def add(self, image_id: str, image_type: ImageType, storage_location: str):
        if image_id in self._manifest_records:
            raise ManifestAlreadyExistsError(image_id)
        self._manifest_records[image_id] = ManifestRecord(image_id, image_type, storage_location)

    def remove(self, image_id: str) -> bool:
        try:
            del self._manifest_records[image_id]
            return True
        except KeyError:
            return False


class TinyDbManifest(Manifest):
    """
    TinyDB backed manifest implementation.
    """
    _MANIFEST_RECORD_SCHEMA = _ManifestRecordSchema()

    @property
    def database_location(self) -> str:
        return self._database_location

    def __init__(self, database_location: str):
        """
        Constructor.
        :param database_location: location of database on disk
        """
        self._database_location = database_location

    def get_by_image_id(self, image_id: str) -> Optional[ManifestRecord]:
        with self._get_database_connection() as database:
            record = database.search(Query().id == image_id)
            if len(record) == 0:
                return None
            assert len(record) == 1
            return TinyDbManifest._MANIFEST_RECORD_SCHEMA.load(record[0])

    def get_by_storage_location(self, storage_location: str) -> Optional[ManifestRecord]:
        with self._get_database_connection() as database:
            record = database.search(Query().storage_location == storage_location)
            if len(record) == 0:
                return None
            assert len(record) == 1
            return TinyDbManifest._MANIFEST_RECORD_SCHEMA.load(record[0])

    def list(self) -> List[ManifestRecord]:
        with self._get_database_connection() as database:
            records = database.all()
            return TinyDbManifest._MANIFEST_RECORD_SCHEMA.load(records, many=True)

    def add(self, image_id: str, image_type: ImageType, storage_location: str):
        if self.get_by_image_id(image_id):
            raise ManifestAlreadyExistsError(image_id)
        assert storage_location is not None
        manifest_record = ManifestRecord(image_id, image_type, storage_location)
        manifest_record_as_json = TinyDbManifest._MANIFEST_RECORD_SCHEMA.dump(manifest_record)
        with self._get_database_connection() as database:
            database.insert(manifest_record_as_json)

    def remove(self, image_id: str) -> bool:
        with self._get_database_connection() as database:
            return database.remove(Query().id == image_id)

    def _get_database_connection(self) -> TinyDB:
        """
        Gets a connection to the TinyDB database.
        :return: open database connection (it is expected that the caller will close it after use)
        """
        # We could do some caching here if instantiating the database every time it's used proves to be expensive
        return TinyDB(self._database_location)
