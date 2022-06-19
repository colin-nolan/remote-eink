import unittest
from abc import abstractmethod, ABCMeta
from threading import Semaphore
from typing import TypeVar, Generic

from remote_eink.transformers.base import (
    ImageTransformer,
    InvalidConfigurationError,
    ListenableMutableImageTransformer,
)
from remote_eink.transformers.simple import SimpleImageTransformer

ImageTransformerType = TypeVar("ImageTransformerType", bound=ImageTransformer)


class AbstractTest:
    """
    https://stackoverflow.com/questions/4566910/abstract-test-case-using-python-unittest
    """

    class TestImageTransformer(Generic[ImageTransformerType], unittest.TestCase, metaclass=ABCMeta):
        """
        Tests for `ImageTransformer`.
        """

        @abstractmethod
        def create_image_transformer(self, *args, **kwargs) -> ImageTransformerType:
            """
            Create an image transformer to test.
            :return: the created image transformer
            """

        def setUp(self):
            super().setUp()
            self.image_transformer: ImageTransformerType = self.create_image_transformer()

        def test_active(self):
            current_active = self.image_transformer.active
            self.image_transformer.active = not current_active
            self.assertNotEqual(current_active, self.image_transformer.active)

        def test_modify_configuration_with_invalid_configuration_parameters(self):
            with self.assertRaises(InvalidConfigurationError):
                self.image_transformer.modify_configuration({"invalid-config-property": True})


class TestListenableImageTransformer(unittest.TestCase):
    """
    Tests for `ListenableImageTransformer`.
    """

    def setUp(self):
        self.image_transformer = ListenableMutableImageTransformer(SimpleImageTransformer())

    def test_listen_to_active_change(self):
        changed = Semaphore(0)

        def on_change(active: bool):
            nonlocal changed, self
            self.assertTrue(active)
            changed.release()

        self.image_transformer.active = False
        self.image_transformer.event_listeners.add_listener(
            on_change, ListenableMutableImageTransformer.Event.ACTIVATE_STATE
        )
        self.image_transformer.active = True
        self.assertTrue(changed.acquire(timeout=15))
