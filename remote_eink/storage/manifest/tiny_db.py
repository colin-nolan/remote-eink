from typing import Optional, List

from marshmallow import post_load, fields, Schema
from marshmallow_enum import EnumField
from tinydb import Query, TinyDB

from remote_eink.images import ImageType, ImageMetadata
from remote_eink.storage.manifest.base import Manifest, ManifestRecord, ManifestAlreadyExistsError


class _ManifestRecordSchema(Schema):
    """
    Marshmallow schema for `ManifestRecord`.
    """

    identifier = fields.Str(data_key="id")
    image_type = EnumField(ImageType)
    metadata = fields.Dict()
    storage_location = fields.Str()

    @post_load
    def make_manifest_record(self, data, **kwargs):
        return ManifestRecord(**data)


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

    def add(self, image_id: str, image_type: ImageType, image_metadata: ImageMetadata, storage_location: str):
        if self.get_by_image_id(image_id):
            raise ManifestAlreadyExistsError(image_id)
        assert storage_location is not None
        manifest_record = ManifestRecord(image_id, image_type, image_metadata, storage_location)
        manifest_record_as_json = TinyDbManifest._MANIFEST_RECORD_SCHEMA.dump(manifest_record)
        with self._get_database_connection() as database:
            database.insert(manifest_record_as_json)

    def remove(self, image_id: str) -> bool:
        with self._get_database_connection() as database:
            deleted = database.remove(Query().id == image_id)
            return len(deleted) > 0

    def _get_database_connection(self) -> TinyDB:
        """
        Gets a connection to the TinyDB database.
        :return: open database connection (it is expected that the caller will close it after use)
        """
        # We could do some caching here if instantiating the database every time it's used proves to be expensive
        return TinyDB(self._database_location)
