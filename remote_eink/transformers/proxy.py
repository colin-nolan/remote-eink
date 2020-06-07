from typing import Dict, Any, Union, Optional

from remote_eink.images import Image
from remote_eink.multiprocess import ProxyObject, prepare_to_send
from remote_eink.transformers import ImageTransformer, ImageTransformerSequence


class ProxyImageTransformer(ImageTransformer, ProxyObject[ImageTransformer]):
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


class ProxyImageTransformerSequence(ImageTransformerSequence, ProxyObject[ImageTransformerSequence]):
    """
    TODO
    """
    def __getitem__(self, i: int) -> ImageTransformer:
        image_transformer, reference = self._communicate_and_get_reference("__getitem__", i)
        return ProxyImageTransformer(self.connection, reference, True)

    def __len__(self) -> int:
        return self._communicate("__len__")

    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        image_transformer, reference = self._communicate_and_get_reference("get_by_id", image_transformer_id)
        if image_transformer is None:
            return None
        assert reference is not None
        return ProxyImageTransformer(self.connection, reference, True)

    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        return self._communicate("get_position", prepare_to_send(image_transformer))

    def set_position(self, image_transformer: ImageTransformer, position: int):
        self._communicate("set_position", prepare_to_send(image_transformer), position)

    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        self._communicate("add", prepare_to_send(image_transformer), position)

    def remove(self, image_transformer: ImageTransformer) -> bool:
        return self._communicate("remove", prepare_to_send(image_transformer))
