import unittest
from abc import abstractmethod, ABCMeta
from threading import Semaphore
from typing import TypeVar, Generic

from remote_eink.tests.transformers.test_base import AbstractTest, ImageTransformerType
from remote_eink.transformers.base import (
    ImageTransformer,
    InvalidConfigurationError,
    ListenableImageTransformer,
)
from remote_eink.transformers.simple import SimpleImageTransformer


class TestSimpleImageTransformer(
    AbstractTest.TestImageTransformer[SimpleImageTransformer],
):
    def create_image_transformer(self, *args, **kwargs) -> SimpleImageTransformer:
        return SimpleImageTransformer()
