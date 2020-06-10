# FIXME
# from enum import unique, Enum, auto
#
# from typing import Any, Callable
# from uuid import uuid4
#
# from multiprocessing_on_dill.context import Process
#
# import unittest
#
# from remote_eink.app import create_app, destroy_app, add_display_controller
# from remote_eink.controllers import BaseDisplayController
# from remote_eink.tests.drivers._common import DummyBaseDisplayDriver
# from remote_eink.storage.images import InMemoryImageStore
# from remote_eink.tests.storage._common import WHITE_IMAGE, BLACK_IMAGE
#
#
# @unique
# class _TestEvent(Enum):
#     WRITE = auto()
#     READ = auto()
#     READ_AFTER = auto()
#
#
# class TestApp(unittest.TestCase):
#     """
#     Tests `TODO`.
#     """
#     @staticmethod
#     def _run_in_different_process(callable: Callable[[], Any]):
#         """
#         TODO
#         :param callable:
#         :return:
#         """
#         process = Process(target=callable)
#         process.start()
#         process.join(timeout=15)
#         if process.exitcode != 0:
#             raise RuntimeError("Process did not exit with status code 0")
#
#     @property
#     def display_controller(self):
#         return get_display_controller(self._display_controller_id, self.app)
#
#     def setUp(self):
#         display_controller = BaseDisplayController(DummyBaseDisplayDriver(), InMemoryImageStore([]))
#         self._display_controller_id = display_controller.identifier
#         self.app = create_app([display_controller])
#
#     def tearDown(self):
#         destroy_app(self.app)
#
#     def test_get_display_controller(self):
#         identifier = self.display_controller.identifier
#         get_display_controller(identifier, self.app).image_store.add(WHITE_IMAGE)
#         self.sanity_check = []
#
#         def update_images():
#             nonlocal self
#             display_controller = get_display_controller(identifier, self.app)
#             self.assertCountEqual((WHITE_IMAGE,), display_controller.image_store)
#             display_controller.image_store.add(BLACK_IMAGE)
#             self.sanity_check.append(True)
#
#         TestApp._run_in_different_process(update_images)
#         self.assertEqual(0, len(self.sanity_check))
#         self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), get_display_controller(identifier, self.app).image_store)
#         self.assertCountEqual((WHITE_IMAGE, BLACK_IMAGE), self.display_controller.image_store)
#
#     def test_add_display_controller(self):
#         ids = [self.display_controller.identifier]
#         for _ in range(10):
#             identifier = str(uuid4())
#             display_controller = BaseDisplayController(DummyBaseDisplayDriver(), InMemoryImageStore([]),
#                                                        identifier=identifier)
#             add_display_controller(display_controller, self.app)
#             ids.append(identifier)
#
#         def check():
#             nonlocal self, ids
#             self.assertCountEqual(ids, (x.identifier for x in get_display_controllers(self.app).values()))
#
#         TestApp._run_in_different_process(check)
#
#
# if __name__ == "__main__":
#     unittest.main()
