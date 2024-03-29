from abc import abstractmethod, ABCMeta
from enum import Enum, auto, unique
from typing import Optional, Iterable, List, Collection, Iterator, Any

from remote_eink.events import EventListenerController
from remote_eink.images import Image, ImageDataReader, FunctionBasedImage
from remote_eink.storage.manifest.base import Manifest, ManifestRecord


class ImageAlreadyExistsError(ValueError):
    """
    Raised when an image already exists when not allowed.
    """

    def __init__(self, image_id: str):
        super().__init__(f"Image with the same ID already exists: {image_id}")


class ImageStore(Collection[Image], metaclass=ABCMeta):
    """
    Store of images.
    """

    @property
    @abstractmethod
    def friendly_type_name(self) -> str:
        """
        Gets the name of this image store type.
        :return: name of this image store type
        """

    @abstractmethod
    def get(self, image_id: str) -> Optional[Image]:
        """
        Gets the image with the given ID.
        :param image_id: ID of the image to get
        :return: the matched image else `None` if image with the given ID is not in the store
        """

    @abstractmethod
    def list(self) -> List[Image]:
        """
        Gets list of image in the store.
        :return: list of images
        """

    @abstractmethod
    def add(self, image: Image):
        """
        Adds the given image to the image store.
        :param image: image to add
        """

    @abstractmethod
    def remove(self, image_id: str) -> bool:
        """
        Removes the image with the given ID from the collection.
        :param image_id: ID of image to remove
        :return: `True` if an image was matched and removed, else `False`
        """


class BaseImageStore(ImageStore):
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
        super().__init__()
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

    def remove(self, image_id: str) -> bool:
        removed = self._remove(image_id)
        return removed


class ManifestBasedImageStore(BaseImageStore, metaclass=ABCMeta):
    """
    Manifest-based image store.

    Relies on a manifest to keep track of where images have been stored.
    """

    @abstractmethod
    def _get_image_reader(self, storage_location: str) -> ImageDataReader:
        """
        Gets reader for the given storage location.
        :param storage_location: storage location
        :return: image reader for the storage location
        """

    @abstractmethod
    def _add_to_storage_location(self, image: Image, suffix: str = "") -> str:
        """
        Adds the given image to a storage location determined by this store.
        :param image: image to store
        :param suffix: suffix to add to the file name (e.g. f"/this/image-{suffix}.jpg")
        :return: location where image has been stored
        """

    @abstractmethod
    def _remove_from_storage_location(self, storage_location: str):
        """
        Removes the image at the given storage location.
        :param storage_location: location of image to remove
        """

    def __init__(self, images: Iterable[Image] = (), manifest: Manifest = None):
        """
        Constructor.
        :param images: images to add to the store
        :param manifest: optional manifest for the image store
        """
        self._manifest = manifest
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
        self._manifest.add(image.identifier, image.type, image.metadata, storage_location)

    def _remove(self, image_id: str) -> bool:
        manifest_record = self._manifest.get_by_image_id(image_id)
        if not manifest_record:
            return False
        self._manifest.remove(image_id)
        self._remove_from_storage_location(manifest_record.storage_location)
        return True

    def _get_image(self, manifest_record: ManifestRecord) -> Image:
        """
        Gets the image in the store associated to the given manifest record.
        :param manifest_record: manifest record of the image
        :return: the image
        """
        image_reader = self._get_image_reader(manifest_record.storage_location)
        return FunctionBasedImage(
            manifest_record.identifier, image_reader, manifest_record.image_type, manifest_record.metadata
        )


class ListenableImageStore(ImageStore):
    """
    Listenable image store.
    """

    @property
    def friendly_type_name(self) -> str:
        return f"Listenable{self._image_store.friendly_type_name}"

    @unique
    class Event(Enum):
        ADD = auto()
        REMOVE = auto()

    def __len__(self) -> int:
        return self._image_store.__len__()

    def __init__(self, image_store: ImageStore):
        """
        Constructor.
        :image_store: underlying image store to make listenable via this interface
        """
        self._image_store = image_store
        self.event_listeners = EventListenerController["ListenableImageStore.Event"]()

    def __iter__(self) -> Iterator[Image]:
        return self._image_store.__iter__()

    def __contains__(self, x: object) -> bool:
        return self._image_store.__contains__(x)

    def get(self, image_id: str) -> Optional[Image]:
        return self._image_store.get(image_id)

    def list(self) -> List[Image]:
        return self._image_store.list()

    def add(self, image: Image):
        self._image_store.add(image)
        self.event_listeners.call_listeners(ListenableImageStore.Event.ADD, [image])

    def remove(self, image_id: str) -> bool:
        removed = self._image_store.remove(image_id)
        self.event_listeners.call_listeners(ListenableImageStore.Event.REMOVE, [image_id])
        return removed
