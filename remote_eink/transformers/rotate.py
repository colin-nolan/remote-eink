import logging
from enum import Enum, unique
from io import BytesIO
from typing import Dict, Any

from remote_eink.models import Image
from remote_eink.transformers.base import ImageTypeToPillowFormat, InvalidConfigurationError, BaseImageTransformer

_logger = logging.getLogger(__name__)

try:
    from PIL import Image as PilImage
except ImportError:
    _logger.error("\"image-tools\" extra not installed")
    raise


@unique
class RotateConfigurationParameter(Enum):
    """
    TODO
    """
    ANGLE = "angle"
    EXPAND = "expand"
    FILL_COLOR = "fill_color"


class RotateImageTransformer(BaseImageTransformer):
    """
    TODO
    """
    @staticmethod
    def _rotate(image: Image, angle: float, expand: bool, fill_color) -> bytes:
        """
        TODO
        :param image:
        :param angle: In degrees counter clockwise.
        :param expand:If true, expands the output
           image to make it large enough to hold the entire rotated image.
           If false or omitted, make the output image the same size as the
           input image.
        :param fill_color:  An optional color for area outside the rotated image
        :return:
        """
        image_data = PilImage.open(BytesIO(image.data))
        image_data = image_data.rotate(angle, expand=expand, fillcolor=fill_color)
        byte_io = BytesIO()
        image_data.save(byte_io, ImageTypeToPillowFormat[image.type])
        return byte_io.getvalue()

    @property
    def configuration(self) -> Dict[str, Any]:
        return {
            RotateConfigurationParameter.ANGLE.value: self.angle,
            RotateConfigurationParameter.EXPAND.value: self.expand,
            RotateConfigurationParameter.FILL_COLOR.value: self.fill_color
        }

    @property
    def description(self) -> str:
        """
        TODO
        :return: TODO
        """
        return f"Rotates an image (currently by {self.angle} degrees)"

    def __init__(self, identifier: str = "rotate", active: bool = True, angle: float = 0.0, expand: bool = True,
                 fill_color: str = "white"):
        """
        TODO
        :param identifier:
        :param active:
        :param angle:
        :param expand:
        :param fill_color:
        """
        super().__init__(identifier, active)
        self.angle = angle
        self.expand = expand
        self.fill_color = fill_color

    def modify_configuration(self, configuration: Dict[str, Any]):
        for key, value in configuration.items():
            if key == RotateConfigurationParameter.ANGLE.value:
                self.angle = float(value)
            elif key == RotateConfigurationParameter.EXPAND.value:
                self.expand = value
            elif key == RotateConfigurationParameter.FILL_COLOR.value:
                self.fill_color = value
            else:
                raise InvalidConfigurationError(configuration, f"unknown property: {key}")

    def _transform(self, image: Image) -> Image:
        return Image(image.identifier,
                     lambda: RotateImageTransformer._rotate(image, self.angle, self.expand, self.fill_color),
                     image.type, cache_data=True)
