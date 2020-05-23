import itertools
import math
import unittest
from abc import ABCMeta
from io import BytesIO
from typing import Tuple

from remote_eink.tests.transformers.test_transformers import TestImageTransformer
from remote_eink.models import Image
from remote_eink.tests.storage._common import WHITE_IMAGE
from remote_eink.transformers.transformers import ImageTransformer

try:
    from remote_eink.transformers.rotate import RotateImageTransformer, ConfigurationParameter
    from PIL import Image as PilImage
    IMAGE_TOOLS_INSTALLED = True
except ImportError:
    class RotateImageTransformer(ImageTransformer, metaclass=ABCMeta):
        """ Please the type checker """
    IMAGE_TOOLS_INSTALLED = False

EXAMPLE_ANGLE = 10
EXAMPLE_EXPAND = False
EXAMPLE_FILL_COLOR = "silver"


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
        return RotateImageTransformer(angle=EXAMPLE_ANGLE, expand=EXAMPLE_EXPAND, fill_color=EXAMPLE_FILL_COLOR)

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

    def test_configuration(self):
        self.assertEqual(
            {ConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE, ConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
             ConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR}, self.transformer.configuration)

    def test_load_configuration(self):
        transformer = RotateImageTransformer()
        assert transformer.angle != EXAMPLE_ANGLE and transformer.expand != EXAMPLE_EXPAND \
               and transformer.fill_color != EXAMPLE_FILL_COLOR
        assert transformer.configuration != self.transformer.configuration
        transformer.load_configuration(self.transformer.configuration)
        self.assertEqual(self.transformer.configuration, transformer.configuration)

    def test_load_partial_configuration(self):
        transformer = RotateImageTransformer(angle=EXAMPLE_ANGLE)
        assert transformer.expand != EXAMPLE_EXPAND and transformer.fill_color != EXAMPLE_FILL_COLOR
        transformer.load_configuration({ConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
                                        ConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR})
        self.assertEqual(
            {ConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE, ConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
             ConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR}, transformer.configuration)




del TestImageTransformer

if __name__ == "__main__":
    unittest.main()
