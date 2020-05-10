from abc import abstractmethod, ABCMeta
from typing import Dict, Optional, Iterable, List

from image_display_service.image import Image


class ImageAlreadyExistsError(ValueError):
    """
    TODO
    """
    def __init__(self, image_id: str):
        super().__init__(f"Image with the same ID already exists: {image_id}")


class ImageStore(metaclass=ABCMeta):
    """
    TODO
    """
    @abstractmethod
    def retrieve(self, image_id: str) -> Optional[Image]:
        """
        Retrieves the image with the given ID.
        :param image_id: ID of the image to retrieve
        :return: the image else `None` if not found
        """

    @abstractmethod
    def list(self) -> List[Image]:
        """
        List of stored images.

        Sorting guaranteed to be stable.
        :return: stored images
        """

    @abstractmethod
    def save(self, image: Image):
        """
        Saves the given image.
        :param image: image to save
        """

    @abstractmethod
    def delete(self, image_id: str) -> bool:
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
        for image in images:
            self.save(image)


class InMemoryImageStore(ImageStore):
    """
    In memory image store.
    """
    def __init__(self, *args, **kwargs):
        self._images: Dict[str, Image] = {}
        super().__init__(*args, **kwargs)

    def retrieve(self, image_id: str) -> Optional[Image]:
        return self._images.get(image_id)

    def list(self) -> List[Image]:
        return sorted(list(self._images.values()), key=lambda image: image.identifier)

    def save(self, image: Image):
        if self.retrieve(image.identifier) is not None:
            raise ImageAlreadyExistsError(image.identifier)
        self._images[image.identifier] = image

    def delete(self, image_id: str) -> bool:
        try:
            del self._images[image_id]
            return True
        except KeyError:
            return False
