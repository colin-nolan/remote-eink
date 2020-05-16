from http import HTTPStatus

import unittest

from remote_eink.tests._common import TestBase


class TestDisplayApi(TestBase):
    """
    Tests for the `/display` endpoint.
    """
    def test_list(self):
        display_controllers = [self.create_dummy_display_controller() for _ in range(10)]
        result = self.client.get("/display")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertCountEqual([{"id": controller.identifier} for controller in display_controllers], result.json)

    def test_get(self):
        for _ in range(5):
            self.create_dummy_display_controller()
        controller = self.create_dummy_display_controller(number_of_images=10)
        for _ in range(5):
            self.create_dummy_display_controller()

        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(controller.identifier, result.json["id"])
        self.assertCountEqual((image.identifier for image in controller._image_store.list()),
                              (image["id"] for image in result.json["images"]))
        self.assertEqual(controller.image_orientation, result.json["orientation"])
        self.assertEqual(controller.cycle_images, result.json["cycleImages"])
        self.assertEqual(controller.cycle_images_randomly, result.json["cycleRandomly"])
        self.assertEqual(controller.cycle_image_after_seconds, result.json["cycleAfterSeconds"])

    def test_get_not_exist(self):
        result = self.client.get(f"/display/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_with_no_images(self):
        controller = self.create_dummy_display_controller(number_of_images=0)
        result = self.client.get(f"/display/{controller.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual([], result.json["images"])
        self.assertIsNone(result.json["currentImage"])


if __name__ == "__main__":
    unittest.main()
