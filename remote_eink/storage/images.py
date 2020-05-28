import hashlib
import os
from abc import abstractmethod, ABCMeta
from enum import Enum, auto, unique
from typing import Dict, Optional, Iterable, List, Collection, Iterator, Any

from remote_eink.events import EventListenerController
from remote_eink.models import Image, ImageDataReader
from remote_eink.storage.manifests import Manifest, TinyDbManifest, ManifestRecord


class ImageAlreadyExistsError(ValueError):
    """
    Raised when an image already exists when not allowed.
    """
    def __init__(self, image_id: str):
        super().__init__(f"Image with the same ID already exists: {image_id}")


class ImageStore(Collection, metaclass=ABCMeta):
    """
    Store of images.
    """
    @abstractmethod
    def _get(self, image_id: str) -> Optional[Image]:
        """
        Retrieves the image with the given ID.
        :param image_id: ID of the image to retrieve
        :return: the image else `None` if not found
        """

    @abstractmethod
    def _list(self) -> List[Image]:
        """
        List of stored images.

        Sorting guaranteed to be stable.
        :return: stored images
        """

    @abstractmethod
    def _add(self, image: Image):
        """
        Saves the given image.
        :param image: image to save
        """

    @abstractmethod
    def _remove(self, image_id: str) -> bool:
        """
        Deletes the image with the given ID.
        :param image_id: ID of the image to delete.
        :return: `True` if image was deleted else `False`
        """

    def __init__(self, images: Iterable[Image] = ()):
        """
        Constructor.
        :param images: images to save
        """
        self.event_listeners = EventListenerController[ImageStoreEvent]()
        for image in images:
            self.add(image)

    def __len__(self) -> int:
        return len(self.list())

    def __iter__(self) -> Iterator[Image]:
        return iter(self.list())

    def __contains__(self, x: Any) -> bool:
        return x in self.list()

    def get(self, image_id: str) -> Optional[Image]:
        return self._get(image_id)

    def list(self) -> List[Image]:
        return self._list()

    def add(self, image: Image):
        self._add(image)
        self.event_listeners.call_listeners(ImageStoreEvent.ADD, [image])

    def remove(self, image_id: str) -> bool:
        removed = self._remove(image_id)
        self.event_listeners.call_listeners(ImageStoreEvent.REMOVE, [image_id])
        return removed


class InMemoryImageStore(ImageStore):
    """
    In memory image store.
    """
    def __init__(self, images: Iterable[Image] = ()):
        self._images: Dict[str, Image] = {}
        super().__init__(images)

    def _get(self, image_id: str) -> Optional[Image]:
        return self._images.get(image_id)

    def _list(self) -> List[Image]:
        return sorted(list(self._images.values()), key=lambda image: image.identifier)

    def _add(self, image: Image):
        assert isinstance(image, Image)
        if self.get(image.identifier) is not None:
            raise ImageAlreadyExistsError(image.identifier)
        self._images[image.identifier] = image

    def _remove(self, image_id: str) -> bool:
        assert isinstance(image_id, str)
        try:
            del self._images[image_id]
            return True
        except KeyError:
            return False


class ManifestBasedImageStore(ImageStore, metaclass=ABCMeta):
    """
    Manifest-based image store.

    Relies on a manifest to keep track of where images have been stored.
    """
    @abstractmethod
    def _get_image_reader(self, storage_location: str) -> ImageDataReader:
        """
        TODO
        :param storage_location:
        :return:
        """

    @abstractmethod
    def _add_to_storage_location(self, image: Image, suffix: str = "") -> str:
        """
        TODO
        :param image:
        :param suffix:
        :return:
        """

    @abstractmethod
    def _remove_from_storage_location(self, storage_location: str):
        """
        TODO
        :param storage_location:
        :return:
        """

    def __init__(self, images: Iterable[Image] = (), manifest: Manifest = None, cache_data: bool = False):
        """
        TODO
        :param images:
        :param manifest:
        :param cache_data:
        """
        self._manifest = manifest
        self.cache_data = cache_data
        super().__init__(images)

    def _get(self, image_id: str) -> Optional[Image]:
        manifest_record = self._manifest.get_by_image_id(image_id)
        if manifest_record is None:
            return None
        return self._get_image(manifest_record)

    def _list(self) -> List[Image]:
        return [self._get_image(manifest_record) for manifest_record in self._manifest.list()]

    def _add(self, image: Image):
        if self._manifest.get_by_image_id(image.identifier) is not None:
            raise ImageAlreadyExistsError(image.identifier)
        storage_location = self._add_to_storage_location(image)
        self._manifest.add(image.identifier, image.type, storage_location)

    def _remove(self, image_id: str) -> bool:
        manifest_record = self._manifest.get_by_image_id(image_id)
        if not manifest_record:
            return False
        self._manifest.remove(image_id)
        self._remove_from_storage_location(manifest_record.storage_location)
        return True

    def _get_image(self, manifest_record: ManifestRecord) -> Image:
        """
        TODO
        :param manifest_record:
        :return:
        """
        image_reader = self._get_image_reader(manifest_record.storage_location)
        return Image(manifest_record.identifier, image_reader, manifest_record.image_type)


class FileSystemImageStore(ManifestBasedImageStore):
    """
    File system based image store.
    """
    def __init__(self, root_directory: str, images: Iterable[Image] = (), manifest: Optional[Manifest] = None):
        self.root_directory = root_directory
        manifest = manifest if manifest is not None else \
            TinyDbManifest(os.path.join(self.root_directory, "manifest.json"))
        super().__init__(images, manifest)

    def _get_image_reader(self, storage_location: str) -> ImageDataReader:
        path = os.path.join(self.root_directory, storage_location)
        assert os.path.exists(path)

        # Not using lambda as observing file not closed warnings
        def reader() -> bytes:
            with open(path, "rb") as file:
                return file.read()

        return reader

    def _add_to_storage_location(self, image: Image, suffix: str = "") -> str:
        md5 = hashlib.md5(image.data).hexdigest()
        storage_location = f"{md5}{suffix}.{image.type.value}"

        if self._manifest.get_by_storage_location(storage_location) is not None:
            # Name collision - add suffix
            dash_index = suffix.rfind("-")
            if dash_index == "-1" or not suffix[dash_index:].isdigit():
                suffix = f"{suffix}-1"
            else:
                suffix = f"{suffix}{suffix[0:dash_index]}{int(suffix[dash_index:]) + 1}"
            return self._add_to_storage_location(image, suffix)

        path = os.path.join(self.root_directory, storage_location)
        assert not os.path.exists(path)
        with open(path, "wb") as file:
            file.write(image.data)
        return storage_location

    def _remove_from_storage_location(self, storage_location: str):
        path = os.path.join(self.root_directory, storage_location)
        assert os.path.exists(path)
        os.remove(path)


@unique
class ImageStoreEvent(Enum):
    """
    TODO
    """
    ADD = auto()
    REMOVE = auto()
