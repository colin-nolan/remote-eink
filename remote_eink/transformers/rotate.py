import logging
from io import BytesIO

from remote_eink.models import Image
from remote_eink.transformers.common import ImageTransformer, ImageTypeToPillowFormat

_logger = logging.getLogger(__name__)

try:
    from PIL import Image as PilImage
except ImportError:
    _logger.error("\"image-tools\" extra not installed")
    raise


class RotateImageTransformer(ImageTransformer):
    """
    TODO
    """
    @staticmethod
    def get_name() -> str:
        return "rotate"

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

    def __init__(self, active: bool = True, angle: float = 0.0, expand: bool = True, fill_color: str = "white"):
        """
        TODO
        :param active:
        :param angle:
        :param expand:
        :param fill_color:
        """
        super().__init__(active)
        self.angle = angle
        self.expand = expand
        self.fill_color = fill_color

    def _transform(self, image: Image) -> Image:
        return Image(image.identifier,
                     lambda: RotateImageTransformer._rotate(image, self.angle, self.expand, self.fill_color),
                     image.type, cache_data=True)
