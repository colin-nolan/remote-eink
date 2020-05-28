from http import HTTPStatus

from remote_eink.app import get_synchronised_app_storage
from remote_eink.display.controllers import DisplayController
from remote_eink.tests._common import AppTestBase


class TestDisplaySleep(AppTestBase):
    """
    Tests for the `/display/{displayId}/sleep` endpoint.
    """
    def setUp(self):
        super().setUp()
        self.create_display_controller()
        assert isinstance(self.display_controller, DisplayController)

    def test_get_when_not_sleeping(self):
        result = self.client.get(f"/display/{self.display_controller.identifier}/sleep")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertFalse(result.json)

    def test_get_when_sleeping(self):
        with get_synchronised_app_storage().use_display_controller(self.display_controller.identifier) \
                as display_controller:
            display_controller.driver.sleep()
        result = self.client.get(f"/display/{self.display_controller.identifier}/sleep")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertTrue(result.json)

    def test_put_sleep_when_not_sleeping(self):
        result = self.client.put(f"/display/{self.display_controller.identifier}/sleep", json=True)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.synchronise_display_controllers()
        self.assertTrue(self.display_controller.driver.sleeping)

    def test_put_sleep_when_sleeping(self):
        controller = self.create_display_controller()
        controller.driver.sleep()
        result = self.client.put(f"/display/{controller.identifier}/sleep", json=True)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertTrue(controller.driver.sleeping)

    def test_put_wake_when_not_sleeping(self):
        result = self.client.put(f"/display/{self.display_controller.identifier}/sleep", json=False)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.synchronise_display_controllers()
        self.assertFalse(self.display_controller.driver.sleeping)

    def test_put_wake_when_sleeping(self):
        with get_synchronised_app_storage().use_display_controller(self.display_controller.identifier) \
                as display_controller:
            display_controller.driver.sleep()
        result = self.client.put(f"/display/{self.display_controller.identifier}/sleep", json=False)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.synchronise_display_controllers()
        self.assertFalse(self.display_controller.driver.sleeping)
