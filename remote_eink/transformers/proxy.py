from typing import Dict, Any, Callable, Union, Optional

from remote_eink.images import Image
from remote_eink.multiprocess import ProxyObject
from remote_eink.transformers import ImageTransformer, ImageTransformerSequence


class ProxyImageTransformer(ImageTransformer, ProxyObject):
    """
    TODO
    """
    @property
    def active(self) -> bool:
        return self._communicate("active")

    @active.setter
    def active(self, active: bool):
        self._communicate("active", active)

    @property
    def configuration(self) -> Dict[str, Any]:
        return self._communicate("configuration")

    @property
    def description(self) -> str:
        return self._communicate("description")

    @property
    def identifier(self) -> str:
        return self._communicate("identifier")

    def modify_configuration(self, configuration: Dict[str, Any]):
        self._communicate("modify_configuration", configuration)

    def _transform(self, image: Image) -> Image:
        return self._communicate("_transform", image)


def to_local_image_transformer(wrappable: Callable) -> Callable:
    """
    TODO
    :param image_transformer:
    :return:
    """
    def wrapped(self, image_transformer, *args, **kwargs) -> Callable:
        if isinstance(image_transformer, ProxyImageTransformer):
            image_transformer = image_transformer.local_copy
        return wrappable(self, image_transformer, *args, **kwargs)

    return wrapped


class ProxyImageTransformerSequence(ImageTransformerSequence, ProxyObject):
    """
    TODO
    """
    def __getitem__(self, i: int) -> ImageTransformer:
        image_transformer = self._communicate("__getitem__", i)
        call_prefix = f"{self.method_name_prefix}." if self.method_name_prefix != "" else ""
        prefix = f"{call_prefix}get_by_id('{image_transformer.identifier}')"
        return ProxyImageTransformer(self.connection, prefix, image_transformer)

    def __len__(self) -> int:
        return self._communicate("__len__")

    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        image_transformer = self._communicate("get_by_id", image_transformer_id)
        if image_transformer is None:
            return None
        call_prefix = f"{self.method_name_prefix}." if self.method_name_prefix != "" else ""
        prefix = f"{call_prefix}get_by_id('{image_transformer_id}')"
        return ProxyImageTransformer(self.connection, prefix, image_transformer)

    @to_local_image_transformer
    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        return self._communicate("get_position", image_transformer)

    @to_local_image_transformer
    def set_position(self, image_transformer: ImageTransformer, position: int):
        self._communicate("set_position", image_transformer, position)

    @to_local_image_transformer
    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        self._communicate("add", image_transformer, position)

    @to_local_image_transformer
    def remove(self, image_transformer: ImageTransformer) -> bool:
        return self._communicate("remove", image_transformer)
