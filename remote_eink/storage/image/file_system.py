import hashlib
import os
from typing import Iterable, Optional

from remote_eink.images import Image, ImageDataReader
from remote_eink.storage.image.base import ManifestBasedImageStore
from remote_eink.storage.manifest.base import Manifest
from remote_eink.storage.manifest.tiny_db import TinyDbManifest


class FileSystemImageStore(ManifestBasedImageStore):
    """
    File system based image store.
    """

    @property
    def friendly_type_name(self) -> str:
        return "FileSystem"

    def __init__(self, root_directory: str, images: Iterable[Image] = (), manifest: Optional[Manifest] = None):
        self.root_directory = root_directory
        # self._cache = {}
        manifest = (
            manifest if manifest is not None else TinyDbManifest(os.path.join(self.root_directory, "manifest.json"))
        )
        super().__init__(images, manifest)

    # # FIXME: putting it in a "cache" is really just a hack to keep the reference alive when held only through a proxy
    # def get(self, image_id: str) -> Optional[Image]:
    #     image = super().get(image_id)
    #     self._cache[image_id] = image
    #     return image
    #
    # # FIXME: putting it in a "cache" is really just a hack to keep the reference alive when held only through a proxy
    # def add(self, image: Image):
    #     super().add(image)
    #     self._cache[image.identifier] = image
    #
    # # FIXME: putting it in a "cache" is really just a hack to keep the reference alive when held only through a proxy
    # def list(self) -> List[Image]:
    #     images = super().list()
    #     for i, image in enumerate(images):
    #         cache_copy = self._cache.get(image.identifier)
    #         if not cache_copy:
    #             self._cache[image.identifier] = image
    #         else:
    #             images[i] = cache_copy
    #     return images

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
        if os.path.exists(path):
            raise AssertionError(f"File already exists: {path}")
        with open(path, "wb") as file:
            file.write(image.data)
        return storage_location

    def _remove_from_storage_location(self, storage_location: str):
        path = os.path.join(self.root_directory, storage_location)
        assert os.path.exists(path)
        os.remove(path)
