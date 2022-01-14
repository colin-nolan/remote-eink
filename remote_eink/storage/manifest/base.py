from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from remote_eink.images import ImageType, ImageMetadata


class ManifestAlreadyExistsError(ValueError):
    """
    Raised when a manifest for the image already exists but it is not allowed.
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
    metadata: ImageMetadata
    storage_location: str

    def __hash__(self) -> int:
        return hash(self.identifier) + hash(self.storage_location)


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

    # TODO: image_type is piece of image_metadata?
    @abstractmethod
    def add(self, image_id: str, image_type: ImageType, image_metadata: ImageMetadata, storage_location: str):
        """
        Adds manifest for the image with the given ID, given type that is stored in the given location.
        :param image_id: ID of the image
        :param image_type: type of the image
        :param image_metadata: metadata associated to the image
        :param storage_location: where the image is stored
        """

    @abstractmethod
    def remove(self, image_id: str) -> bool:
        """
        Removes the manifest for the image with the given ID.
        :param image_id: ID of the image
        :return: `True` if an image is removed else `False`
        """
