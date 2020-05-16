from http import HTTPStatus

from remote_eink.tests._common import TestBase


class TestDisplaySleep(TestBase):
    """
    Tests for the `/display/{displayId}/sleep` endpoint.
    """
    def test_get_when_not_sleeping(self):
        controller = self.create_dummy_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/sleep")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertFalse(result.json)

    def test_get_when_sleeping(self):
        controller = self.create_dummy_display_controller()
        controller._driver.sleep()
        result = self.client.get(f"/display/{controller.identifier}/sleep")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertTrue(result.json)

    def test_put_sleep_when_not_sleeping(self):
        controller = self.create_dummy_display_controller()
        result = self.client.put(f"/display/{controller.identifier}/sleep", json=True)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertTrue(controller._driver.sleeping)

    def test_put_sleep_when_sleeping(self):
        controller = self.create_dummy_display_controller()
        controller._driver.sleep()
        result = self.client.put(f"/display/{controller.identifier}/sleep", json=True)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertTrue(controller._driver.sleeping)

    def test_put_wake_when_not_sleeping(self):
        controller = self.create_dummy_display_controller()
        result = self.client.put(f"/display/{controller.identifier}/sleep", json=False)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertFalse(controller._driver.sleeping)

    def test_put_wake_when_sleeping(self):
        controller = self.create_dummy_display_controller()
        controller._driver.sleep()
        result = self.client.put(f"/display/{controller.identifier}/sleep", json=False)
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertFalse(controller._driver.sleeping)
