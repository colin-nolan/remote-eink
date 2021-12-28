from typing import Dict, Optional, List

from remote_eink.images import ImageType
from remote_eink.storage.manifest.base import Manifest, ManifestRecord, ManifestAlreadyExistsError


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
            return next(
                filter(
                    lambda manifest_record: manifest_record.storage_location == storage_location,
                    self._manifest_records.values(),
                )
            )
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
