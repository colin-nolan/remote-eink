import itertools
import math
import unittest
from abc import ABCMeta
from io import BytesIO
from typing import Tuple

from remote_eink.tests.transformers._common import TestImageTransformer
from remote_eink.models import Image
from remote_eink.tests.storage._common import WHITE_IMAGE
from remote_eink.transformers.common import ImageTransformer

try:
    from remote_eink.transformers.rotate import RotateImageTransformer
    from PIL import Image as PilImage
    IMAGE_TOOLS_INSTALLED = True
except ImportError:
    class RotateImageTransformer(ImageTransformer, metaclass=ABCMeta):
        """ Please the type checker """
    IMAGE_TOOLS_INSTALLED = False


@unittest.skipIf(not IMAGE_TOOLS_INSTALLED, "Optional `image-tools` not installed")
class TestRotateImageTransformer(TestImageTransformer[RotateImageTransformer]):
    """
    Test for `RotateImageTransformer`.
    """
    @staticmethod
    def _get_size(image: Image) -> Tuple[int, int]:
        """
        TODO
        :param image:
        :return:
        """
        return PilImage.open(BytesIO(image.data)).size

    @staticmethod
    def _calculate_new_size(image_size: Tuple[int, int], angle: float) -> Tuple[int, int]:
        """
        TODO
        :param image_size:
        :param angle:
        :return:
        """
        new_width = abs(image_size[0] * math.cos(math.radians(angle))) + abs(image_size[1] * math.sin(math.radians(angle)))
        new_height = abs(image_size[0] * math.sin(math.radians(angle))) + abs(image_size[1] * math.cos(math.radians(angle)))
        return int(new_width), int(new_height)

    def create_image_transformer(self) -> RotateImageTransformer:
        return RotateImageTransformer()

    def test_rotate(self):
        self.transformer.expand = True
        for i in range(-360, 361, 90):
            with self.subTest(angle=i):
                self.transformer.angle = i
                expected_size = TestRotateImageTransformer._calculate_new_size(
                    TestRotateImageTransformer._get_size(WHITE_IMAGE), i)
                image = self.transformer.transform(WHITE_IMAGE)
                self.assertEqual(expected_size, TestRotateImageTransformer._get_size(image))

    def test_rotate_no_expand(self):
        self.transformer.angle = 90
        self.transformer.expand = False
        image = self.transformer.transform(WHITE_IMAGE)
        self.assertEqual(TestRotateImageTransformer._get_size(WHITE_IMAGE),
                         TestRotateImageTransformer._get_size(image))

    def test_fill_colour(self):
        self.transformer.angle = 45
        self.transformer.fill_color = "black"
        self.transformer.expand = True
        assert len(PilImage.open(BytesIO(WHITE_IMAGE.data)).getcolors()) == 1
        image = self.transformer.transform(WHITE_IMAGE)

        new_colours = PilImage.open(BytesIO(image.data)).getcolors()
        two_primary_colours = list(itertools.islice(sorted(new_colours, key=lambda y: y[0], reverse=True), 2))
        self.assertCountEqual(((0, 0, 0), (255, 255, 255)), (x[1] for x in two_primary_colours))


del TestImageTransformer

if __name__ == "__main__":
    unittest.main()
