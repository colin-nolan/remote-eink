import unittest
from http import HTTPStatus

from remote_eink.tests._common import AppTestBase
from remote_eink.tests.storage._common import WHITE_IMAGE


class TestDisplayCurrentImage(AppTestBase):
    """
    Tests for the `/display/{displayId}/current-image` endpoint.
    """

    def test_get_when_none(self):
        display_controller = self.create_display_controller()
        result = self.client.get(f"/display/{display_controller.identifier}/current-image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_when_set(self):
        self.display_controller.image_store.add(WHITE_IMAGE)
        self.display_controller.display(WHITE_IMAGE.identifier)
        result = self.client.get(f"/display/{self.display_controller.identifier}/current-image")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(WHITE_IMAGE.identifier, result.json["id"])

    def test_set_to_existing_image(self):
        self.display_controller.image_store.add(WHITE_IMAGE)
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/current-image", json={"id": WHITE_IMAGE.identifier}
        )
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(WHITE_IMAGE, self.display_controller.current_image)

    def test_set_to_non_existent_image(self):
        display_controller = self.create_display_controller()
        result = self.client.put(
            f"/display/{display_controller.identifier}/current-image", json={"id": WHITE_IMAGE.identifier}
        )
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_set_with_array(self):
        display_controller = self.create_display_controller()
        result = self.client.put(
            f"/display/{display_controller.identifier}/current-image", json=[{"id": WHITE_IMAGE.identifier}]
        )
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_set_without_id(self):
        display_controller = self.create_display_controller()
        result = self.client.put(f"/display/{display_controller.identifier}/current-image", json={})
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)


if __name__ == "__main__":
    unittest.main()
