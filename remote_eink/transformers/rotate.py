import logging
from enum import Enum, unique
from io import BytesIO
from typing import Dict, Any

from remote_eink.images import Image, FunctionBasedImage
from remote_eink.transformers.base import ImageTypeToPillowFormat, InvalidConfigurationError, BaseImageTransformer

_logger = logging.getLogger(__name__)

from PIL import Image as PilImage


ROTATION_METADATA_KEY = "rotation"


@unique
class RotateConfigurationParameter(Enum):
    """
    Configuration parameters that can be used to alter the function of a `RotateImageTransformer`.
    """

    ANGLE = "angle"
    EXPAND = "expand"
    FILL_COLOR = "fill_color"


class RotateImageTransformer(BaseImageTransformer):
    """
    Transformer that rotates the image by a common angle (the rotation on the image itself is ignored).
    """

    @staticmethod
    def rotate(image: Image, angle: float, expand: bool, fill_color: str) -> bytes:
        """
        Rotates the given image according to the given specification.
        :param image: image to rotate
        :param angle: counter clockwise angle (in degrees) to rotate image by
        :param expand: if true, expands the output image to make it large enough to hold the entire rotated image
                       If false, makes the output image the same size as the input image.
        :param fill_color: color for area outside the rotated image
        :return: bytes of rotated image
        """
        if angle % 360 == 0:
            return image.data
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
            RotateConfigurationParameter.FILL_COLOR.value: self.fill_color,
        }

    @property
    def description(self) -> str:
        return f"Rotates an image (currently by {self.angle} degrees)"

    def __init__(
        self,
        identifier: str = "rotate",
        active: bool = True,
        angle: float = 0.0,
        expand: bool = True,
        fill_color: str = "white",
    ):
        """
        Constructor.
        :param identifier: transformer's identifier
        :param active: see `RotateImageTransformer.rotate`
        :param angle: see `RotateImageTransformer.rotate`
        :param expand: see `RotateImageTransformer.rotate`
        :param fill_color: see `RotateImageTransformer.rotate`
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
        return FunctionBasedImage(
            image.identifier,
            lambda: RotateImageTransformer.rotate(image, self.angle, self.expand, self.fill_color),
            image.type,
        )


class ImageRotationAwareRotateImageTransformer(RotateImageTransformer):
    """
    Transformer that rotates the image by a common angle in addition to the specific rotation set on the image.
    """

    @property
    def description(self) -> str:
        return (
            f"Rotates an image (currently by {self.angle} degrees, in addition to applying the image specific "
            f"rotation)"
        )

    def _transform(self, image: Image) -> Image:
        image_rotation = image.metadata.get(ROTATION_METADATA_KEY, 0)
        return FunctionBasedImage(
            image.identifier,
            lambda: RotateImageTransformer.rotate(image, self.angle + image_rotation, self.expand, self.fill_color),
            image.type,
            image.metadata,
        )
