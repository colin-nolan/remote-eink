from enum import unique, Enum, auto

from typing import Any, Callable

from multiprocessing_on_dill.context import Process
from multiprocessing import Event

import unittest

from remote_eink.app import create_app, get_app_storage
from remote_eink.app_storage import SynchronisedAppStorage
from remote_eink.display.controllers import DisplayController
from remote_eink.display.drivers import DummyDisplayDriver
from remote_eink.storage.images import InMemoryImageStore
from remote_eink.tests._common import create_dummy_display_controller
from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE


@unique
class _TestEvent(Enum):
    WRITE = auto()
    READ = auto()
    READ_AFTER = auto()


class TestApp(unittest.TestCase):
    """
    Tests `TODO`.
    """
    @staticmethod
    def _run_in_different_process(callable: Callable[[], Any]):
        """
        TODO
        :param callable:
        :return:
        """
        process = Process(target=callable)
        process.start()
        process.join(timeout=15)

    @property
    def display_controller(self):
        return self.app_storage.display_controllers[self._display_controller_id]

    def setUp(self):
        display_controller = DisplayController(DummyDisplayDriver(), InMemoryImageStore([]))
        self._display_controller_id = display_controller.identifier
        self.app = create_app([display_controller], SynchronisedAppStorage).app
        self.app_storage = get_app_storage(app=self.app)

    def test_setup_display_controller(self):
        display_controller = create_dummy_display_controller(number_of_images=10, number_of_image_transformers=10)
        with self.app_storage.update_display_controllers() as display_controllers:
            display_controllers[display_controller.identifier] = display_controller

        synchronised_display_controller = self.app_storage.display_controllers[
            display_controller.identifier]
        self.assertCountEqual(set(display_controller.image_store), set(synchronised_display_controller.image_store))
        self.assertEqual(tuple(display_controller.image_transformers),
                         tuple(synchronised_display_controller.image_transformers))

    def test_add_image_in_different_process(self):
        with self.app_storage.update_display_controller(self.display_controller.identifier) as display_controller:
            display_controller.image_store.add(WHITE_IMAGE)

        def update_images():
            nonlocal self
            with self.app_storage.update_display_controller(self.display_controller.identifier) as display_controller:
                synchronised_app_storage = self.app_storage
                self.assertEqual(1, synchronised_app_storage.display_controller_user_count)
                self.assertFalse(synchronised_app_storage.update_pending)
                self.assertCountEqual((WHITE_IMAGE,), display_controller.image_store)
                display_controller.image_store.add(BLACK_IMAGE)

        TestApp._run_in_different_process(update_images)
        self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), self.display_controller.image_store)

    def test_add_new_display_controller(self):
        updated = Event()
        new_display_controller = DisplayController(DummyDisplayDriver(), InMemoryImageStore([]))

        def updater():
            nonlocal self, updated, new_display_controller
            with self.app_storage.update_display_controllers() as display_controllers:
                synchronised_app_storage = self.app_storage
                self.assertEqual(0, synchronised_app_storage.display_controller_user_count)
                self.assertTrue(synchronised_app_storage.update_pending)
                display_controllers[new_display_controller.identifier] = new_display_controller
            updated.set()

        def user():
            nonlocal self
            with self.app_storage.update_display_controller(self.display_controller.identifier) as display_controller:
                display_controller.driver.clear()

        for i in range(10):
            TestApp._run_in_different_process(user)
        TestApp._run_in_different_process(updater)

        updated.wait(timeout=15)
        self.assertCountEqual((self.display_controller.identifier, new_display_controller.identifier),
                              self.app_storage.display_controllers.keys())

        with self.app_storage.update_display_controller(new_display_controller.identifier) as display_controller:
            display_controller.image_store.add(WHITE_IMAGE)

        self.assertCountEqual((WHITE_IMAGE, ),
                              self.app_storage.display_controllers[new_display_controller.identifier].image_store)


if __name__ == "__main__":
    unittest.main()
