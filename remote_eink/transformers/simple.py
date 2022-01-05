from typing import Dict, Any, Optional, Callable
from uuid import uuid4

from remote_eink.images import Image
from remote_eink.transformers.base import BaseImageTransformer, InvalidConfigurationError


class SimpleImageTransformer(BaseImageTransformer):
    """
    Simple image transformer.
    """

    @property
    def configuration(self) -> Dict[str, Any]:
        return self._configuration

    @property
    def description(self) -> str:
        return self._description

    def __init__(
        self,
        transformer: Optional[Callable[[Image], Image]] = None,
        active: bool = True,
        configuration: Optional[Any] = None,
        description: Optional[str] = None,
        identifier: str = None,
    ):
        super().__init__(identifier if identifier is not None else str(uuid4()), active)
        self._transformer = transformer if transformer is not None else lambda image: image
        self._configuration = configuration if configuration is not None else {}
        self._description = description if description is not None else ""

    def modify_configuration(self, configuration: Dict[str, Any]):
        if "invalid-config-property" in configuration:
            raise InvalidConfigurationError(configuration)
        self._configuration = configuration

    def _transform(self, image: Image) -> Image:
        return self._transformer(image)
