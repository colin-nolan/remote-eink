import unittest
from abc import ABCMeta, abstractmethod
from threading import Semaphore
from typing import TypeVar, Generic

from remote_eink.transformers.common import ImageTransformer, ImageTransformerEvent

ImageTransformerType = TypeVar("ImageTransformerType", bound=ImageTransformer)


class TestImageTransformer(unittest.TestCase, Generic[ImageTransformerType], metaclass=ABCMeta):
    """
    Tests for `ImageTransformer`.
    """
    @abstractmethod
    def create_image_transformer(self) -> ImageTransformerType:
        """
        TODO
        :return:
        """

    def setUp(self):
        self.transformer = self.create_image_transformer()

    def test_get_name(self):
        self.assertIsInstance(self.transformer.__class__.get_name(), str)

    def test_active(self):
        current_active = self.transformer.active
        self.transformer.active = not current_active
        self.assertNotEqual(current_active, self.transformer.active)

    def test_listen_to_active_change(self):
        changed = Semaphore(0)

        def on_change(active: bool):
            nonlocal changed, self
            self.assertTrue(active)
            changed.release()

        self.transformer.active = False
        self.transformer.event_listeners.add_listener(on_change, ImageTransformerEvent.ACTIVATE_STATE)
        self.transformer.active = True
        self.assertTrue(changed.acquire(timeout=15))
