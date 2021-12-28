from typing import Iterable, Dict, Optional, List

from remote_eink.images import Image
from remote_eink.storage.image.base import BaseImageStore, ImageAlreadyExistsError


class InMemoryImageStore(BaseImageStore):
    """
    In memory image store.
    """

    @property
    def friendly_type_name(self) -> str:
        return "InMemory"

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
