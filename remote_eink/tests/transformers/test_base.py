import unittest
from abc import abstractmethod, ABCMeta
from threading import Semaphore
from typing import TypeVar, Generic, Sequence

from remote_eink.transformers.base import ImageTransformer, ImageTransformerSequence, \
    InvalidConfigurationError, InvalidPositionError, ListenableImageTransformer, SimpleImageTransformerSequence, \
    SimpleImageTransformer

ImageTransformerType = TypeVar("ImageTransformerType", bound=ImageTransformer)
ImageTransformerSequenceType = TypeVar("ImageTransformerSequenceType", bound=ImageTransformerSequence)


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

    class TestImageTransformerSequence(Generic[ImageTransformerSequenceType], unittest.TestCase, metaclass=ABCMeta):
        """
        Tests for `ImageTransformerSequence`.
        """
        @abstractmethod
        def create_image_transformer_sequence(self, image_transformers: Sequence[ImageTransformer]) \
                -> ImageTransformerSequenceType:
            """
            TODO
            :return:
            """

        def setUp(self):
            super().setUp()
            self.image_transformers_list = [SimpleImageTransformer(), SimpleImageTransformer(), SimpleImageTransformer()]
            self.image_transformers: ImageTransformerSequenceType = self.create_image_transformer_sequence(
                self.image_transformers_list)

        def test_len(self):
            self.assertEqual(len(self.image_transformers_list), len(self.image_transformers))

        def test_iterate(self):
            for i, image_transformer in enumerate(self.image_transformers):
                self.assertEqual(self.image_transformers_list[i], image_transformer)

        def test_contains(self):
            self.assertIn(self.image_transformers_list[0], self.image_transformers)
            self.assertNotIn(SimpleImageTransformer(), self.image_transformers)

        def test_slice(self):
            self.assertEqual(self.image_transformers_list[1], self.image_transformers[1])

        def test_get_by_id(self):
            image_transformer = self.image_transformers.get_by_id(self.image_transformers_list[1].identifier)
            self.assertEqual(image_transformer, self.image_transformers_list[1])

        def test_get_by_id_when_does_not_exist(self):
            self.assertIsNone(self.image_transformers.get_by_id("does-not-exist"))

        def test_get_position(self):
            for i, image_transformer in enumerate(self.image_transformers):
                self.assertEqual(i, self.image_transformers.get_position(image_transformer))

        def test_get_position_when_does_not_exist(self):
            with self.assertRaises(KeyError):
                self.image_transformers.get_position(SimpleImageTransformer())

        def test_get_position_using_id(self):
            for i, image_transformer in enumerate(self.image_transformers):
                self.assertEqual(i, self.image_transformers.get_position(image_transformer.identifier))

        def test_set_position(self):
            image_transformer = self.image_transformers[1]
            assert self.image_transformers.get_position(image_transformer) == 1
            self.image_transformers.set_position(image_transformer, 0)
            self.assertEqual(0, self.image_transformers.get_position(image_transformer))

        def test_set_position_beyond_end(self):
            image_transformer = self.image_transformers[1]
            assert len(self.image_transformers) < 10
            self.image_transformers.set_position(image_transformer, 10)
            self.assertEqual(len(self.image_transformers) - 1, self.image_transformers.get_position(image_transformer))

        def test_set_position_when_image_transformer_not_in_sequence(self):
            with self.assertRaises(KeyError):
                 self.image_transformers.set_position(SimpleImageTransformer(), 0)

        def test_set_position_less_than_zero(self):
            with self.assertRaises(InvalidPositionError):
                 self.image_transformers.set_position(self.image_transformers[0], -1)

        def test_add(self):
            image_transformer = SimpleImageTransformer()
            self.image_transformers.add(image_transformer)
            self.assertEqual(image_transformer, self.image_transformers[-1])

        def test_add_with_position(self):
            image_transformer = SimpleImageTransformer()
            self.image_transformers.add(image_transformer, 1)
            self.assertEqual(image_transformer, self.image_transformers[1])

        def test_add_with_duplicate_id(self):
            self.image_transformers.add(SimpleImageTransformer(identifier="test"))
            with self.assertRaises(ValueError):
                self.image_transformers.add(SimpleImageTransformer(identifier="test"))

        def test_remove(self):
            for image_transformer in self.image_transformers_list:
                self.assertIn(image_transformer, self.image_transformers)
                self.assertTrue(self.image_transformers.remove(image_transformer))
                self.assertNotIn(image_transformer, self.image_transformers)

        def test_remove_when_does_not_exist(self):
            self.assertFalse(self.image_transformers.remove(SimpleImageTransformer()))

        def test_str(self):
            self.assertIsInstance(str(self.image_transformers), str)


class TestListenableImageTransformer(unittest.TestCase):
    """
    Tests for `ListenableImageTransformer`.
    """
    def setUp(self):
        self.image_transformer = ListenableImageTransformer(SimpleImageTransformer())

    def test_listen_to_active_change(self):
        changed = Semaphore(0)

        def on_change(active: bool):
            nonlocal changed, self
            self.assertTrue(active)
            changed.release()

        self.image_transformer.active = False
        self.image_transformer.event_listeners.add_listener(
            on_change, ListenableImageTransformer.Event.ACTIVATE_STATE)
        self.image_transformer.active = True
        self.assertTrue(changed.acquire(timeout=15))


class TestSimpleImageTransformerSequence(AbstractTest.TestImageTransformerSequence[SimpleImageTransformerSequence]):
    """
    Tests `SimpleImageTransformerSequence`.
    """
    def create_image_transformer_sequence(self, image_transformers: Sequence[ImageTransformer])\
            -> ImageTransformerSequenceType:
        return SimpleImageTransformerSequence(image_transformers)

    def test_add_event(self):
        semaphore = Semaphore(0)
        callback_image_transformer = None
        callback_position = None

        def callback(image_transformer: ImageTransformer, position: int):
            nonlocal semaphore, callback_image_transformer, callback_position
            callback_image_transformer = image_transformer
            callback_position = position
            semaphore.release()

        self.image_transformers.event_listeners.add_listener(callback, SimpleImageTransformerSequence.Event.ADD)
        image_transformer = SimpleImageTransformer()
        self.image_transformers.add(image_transformer)
        self.assertTrue(semaphore.acquire(timeout=15))
        self.assertEqual(image_transformer, callback_image_transformer)
        self.assertEqual(len(self.image_transformers) - 1, callback_position)

    def test_remove_event(self):
        semaphore = Semaphore(0)
        callback_image_transformer = None
        callback_removed = None

        def callback(image_transformer: ImageTransformer, removed: bool):
            nonlocal semaphore, callback_image_transformer, callback_removed
            callback_image_transformer = image_transformer
            callback_removed = removed
            semaphore.release()

        self.image_transformers.event_listeners.add_listener(callback, SimpleImageTransformerSequence.Event.REMOVE)
        image_transformer = SimpleImageTransformer()
        self.image_transformers.remove(image_transformer)
        self.assertTrue(semaphore.acquire(timeout=15))
        self.assertEqual(image_transformer, callback_image_transformer)
        self.assertFalse(callback_removed)
