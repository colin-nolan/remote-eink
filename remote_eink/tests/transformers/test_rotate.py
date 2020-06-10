import itertools
import math
import unittest
from abc import ABCMeta
from io import BytesIO
from typing import Tuple

from remote_eink.images import Image
from remote_eink.tests.storage._common import WHITE_IMAGE
from remote_eink.tests.transformers.test_base import AbstractTest
from remote_eink.transformers.base import ImageTransformer

try:
    from remote_eink.transformers.rotate import RotateImageTransformer, RotateConfigurationParameter
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
class TestRotateImageTransformer(AbstractTest.TestImageTransformer[RotateImageTransformer]):
    """
    Test for `RotateImageTransformer`.
    """
    @staticmethod
    def _get_size(image: Image) -> Tuple[int, int]:
        """
        Gets size of the given image.
        :param image: image to get size of
        :return: width, height tuple
        """
        return PilImage.open(BytesIO(image.data)).size

    @staticmethod
    def _calculate_new_size(image_size: Tuple[int, int], angle: float) -> Tuple[int, int]:
        """
        Calculates horizontal and vertical size of an image of the given size after it has been rotated by the given
        angle.
        :param image_size: original image size width, height tuple
        :param angle: rotation angle in degrees
        :return: width, height tuple after translation
        """
        new_width = abs(
            image_size[0] * math.cos(math.radians(angle))) + abs(image_size[1] * math.sin(math.radians(angle)))
        new_height = abs(
            image_size[0] * math.sin(math.radians(angle))) + abs(image_size[1] * math.cos(math.radians(angle)))
        return int(new_width), int(new_height)

    def create_image_transformer(self) -> RotateImageTransformer:
        return RotateImageTransformer(angle=EXAMPLE_ANGLE, expand=EXAMPLE_EXPAND, fill_color=EXAMPLE_FILL_COLOR)

    def test_rotate(self):
        self.image_transformer.expand = True
        for i in range(-360, 361, 90):
            with self.subTest(angle=i):
                self.image_transformer.angle = i
                expected_size = TestRotateImageTransformer._calculate_new_size(
                    TestRotateImageTransformer._get_size(WHITE_IMAGE), i)
                image = self.image_transformer.transform(WHITE_IMAGE)
                self.assertEqual(expected_size, TestRotateImageTransformer._get_size(image))

    def test_rotate_no_expand(self):
        self.image_transformer.angle = 90
        self.image_transformer.expand = False
        image = self.image_transformer.transform(WHITE_IMAGE)
        self.assertEqual(TestRotateImageTransformer._get_size(WHITE_IMAGE),
                         TestRotateImageTransformer._get_size(image))

    def test_fill_colour(self):
        self.image_transformer.angle = 45
        self.image_transformer.fill_color = "black"
        self.image_transformer.expand = True
        assert len(PilImage.open(BytesIO(WHITE_IMAGE.data)).getcolors()) == 1
        image = self.image_transformer.transform(WHITE_IMAGE)

        new_colours = PilImage.open(BytesIO(image.data)).getcolors()
        two_primary_colours = list(itertools.islice(sorted(new_colours, key=lambda y: y[0], reverse=True), 2))
        self.assertCountEqual(((0, 0, 0), (255, 255, 255)), (x[1] for x in two_primary_colours))

    def test_configuration(self):
        self.assertEqual(
            {RotateConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE, RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
             RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR}, self.image_transformer.configuration)

    def test_modify_configuration(self):
        image_transformer = RotateImageTransformer()
        assert image_transformer.angle != EXAMPLE_ANGLE and image_transformer.expand != EXAMPLE_EXPAND \
               and image_transformer.fill_color != EXAMPLE_FILL_COLOR
        assert image_transformer.configuration != self.image_transformer.configuration
        image_transformer.modify_configuration(self.image_transformer.configuration)
        self.assertEqual(self.image_transformer.configuration, image_transformer.configuration)

    def test_modify_configuration_partially(self):
        image_transformer = RotateImageTransformer(angle=EXAMPLE_ANGLE)
        assert image_transformer.expand != EXAMPLE_EXPAND and image_transformer.fill_color != EXAMPLE_FILL_COLOR
        image_transformer.modify_configuration({RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
                                                RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR})
        self.assertEqual(
            {RotateConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE,
             RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
             RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR}, image_transformer.configuration)


if __name__ == "__main__":
    unittest.main()
