import itertools
import unittest
from abc import ABCMeta
from io import BytesIO
from typing import Tuple, TypeVar, Generic

import math
from PIL import Image as PilImage

from remote_eink.images import Image, FunctionBasedImage
from remote_eink.tests.storage._common import WHITE_IMAGE
from remote_eink.tests.transformers.test_base import AbstractTest
from remote_eink.transformers.rotate import (
    RotateImageTransformer,
    RotateConfigurationParameter,
    ImageRotationAwareRotateImageTransformer,
    ROTATION_METADATA_KEY,
)

EXAMPLE_ANGLE = 10
EXAMPLE_EXPAND = False
EXAMPLE_FILL_COLOR = "silver"

RotatingImageTransformerType = TypeVar("RotatingImageTransformerType", bound=RotateImageTransformer)


def _get_size(image: Image) -> Tuple[int, int]:
    """
    Gets size of the given image.
    :param image: image to get size of
    :return: width, height tuple
    """
    return PilImage.open(BytesIO(image.data)).size


def _calculate_new_size(image_size: Tuple[int, int], angle: float) -> Tuple[int, int]:
    """
    Calculates horizontal and vertical size of an image of the given size after it has been rotated by the given
    angle.
    :param image_size: original image size width, height tuple
    :param angle: rotation angle in degrees
    :return: width, height tuple after translation
    """
    new_width = abs(image_size[0] * math.cos(math.radians(angle))) + abs(image_size[1] * math.sin(math.radians(angle)))
    new_height = abs(image_size[0] * math.sin(math.radians(angle))) + abs(image_size[1] * math.cos(math.radians(angle)))
    return int(new_width), int(new_height)


class BaseTest(
    Generic[RotatingImageTransformerType],
    AbstractTest.TestImageTransformer[RotatingImageTransformerType],
    metaclass=ABCMeta,
):
    """
    Test for `RotateImageTransformer`.
    """

    def test_no_rotation(self):
        self.image_transformer.angle = 0
        image = self.image_transformer.transform(WHITE_IMAGE)
        self.assertEqual(WHITE_IMAGE.data, image.data)

    def test_rotate_no_expand(self):
        self.image_transformer.angle = 90
        self.image_transformer.expand = False
        image = self.image_transformer.transform(WHITE_IMAGE)
        self.assertEqual(_get_size(WHITE_IMAGE), _get_size(image))

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
        image_transformer = self.create_image_transformer(
            angle=EXAMPLE_ANGLE, expand=EXAMPLE_EXPAND, fill_color=EXAMPLE_FILL_COLOR
        )
        self.assertEqual(
            {
                RotateConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE,
                RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
                RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR,
            },
            image_transformer.configuration,
        )

    def test_modify_configuration(self):
        image_transformer = self.create_image_transformer(
            angle=EXAMPLE_EXPAND, expand=EXAMPLE_EXPAND, fill_color=EXAMPLE_FILL_COLOR
        )
        assert image_transformer.configuration != self.image_transformer.configuration
        image_transformer.modify_configuration(self.image_transformer.configuration)
        self.assertEqual(self.image_transformer.configuration, image_transformer.configuration)

    def test_modify_configuration_partially(self):
        image_transformer = self.create_image_transformer(angle=EXAMPLE_ANGLE)
        assert image_transformer.expand != EXAMPLE_EXPAND and image_transformer.fill_color != EXAMPLE_FILL_COLOR
        image_transformer.modify_configuration(
            {
                RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
                RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR,
            }
        )
        self.assertEqual(
            {
                RotateConfigurationParameter.ANGLE.value: EXAMPLE_ANGLE,
                RotateConfigurationParameter.EXPAND.value: EXAMPLE_EXPAND,
                RotateConfigurationParameter.FILL_COLOR.value: EXAMPLE_FILL_COLOR,
            },
            image_transformer.configuration,
        )


class TestRotateImageTransformer(BaseTest[RotateImageTransformer]):
    """
    Tests for `RotateImageTransformer`.
    """

    def create_image_transformer(self, *args, **kwargs) -> RotateImageTransformer:
        return RotateImageTransformer(*args, **kwargs)

    def test_rotate(self):
        self.image_transformer.expand = True
        for i in range(-360, 361, 90):
            with self.subTest(angle=i):
                self.image_transformer.angle = i
                expected_size = _calculate_new_size(_get_size(WHITE_IMAGE), i)
                image = self.image_transformer.transform(WHITE_IMAGE)
                self.assertEqual(expected_size, _get_size(image))


class TestImageRotationAwareRotateImageTransformer(BaseTest[ImageRotationAwareRotateImageTransformer]):
    """
    Tests for `ImageRotationAwareRotateImageTransformer`.
    """

    def create_image_transformer(self, *args, **kwargs) -> RotateImageTransformer:
        return ImageRotationAwareRotateImageTransformer(*args, **kwargs)

    def test_rotate(self):
        self.image_transformer.angle = 45
        image = FunctionBasedImage(
            WHITE_IMAGE.identifier,
            lambda: WHITE_IMAGE.data,
            WHITE_IMAGE.type,
            {**WHITE_IMAGE.metadata, ROTATION_METADATA_KEY: 45},
        )
        rotated_image = self.image_transformer.transform(image)
        expected_size = _calculate_new_size(_get_size(image), 45 + 45)
        self.assertEqual(expected_size, _get_size(rotated_image))


del BaseTest

if __name__ == "__main__":
    unittest.main()
