import json
from http import HTTPStatus
from io import BytesIO

from remote_eink.images import ImageType
from remote_eink.tests._common import create_image
from remote_eink.tests.api.display.image._common import BaseTestDisplayImage


class TestDisplayImageMetadata(BaseTestDisplayImage):
    """
    Tests for the `/display/{displayId}/image/metadata` endpoint.
    """

    def test_get(self):
        for image_type in ImageType:
            with self.subTest(image_type=image_type.name):
                display_controller = self.create_display_controller()
                image = create_image(image_type=image_type)
                display_controller.image_store.add(image)
                result = self.client.get(f"/display/{display_controller.identifier}/image/{image.identifier}/metadata")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertEqual(display_controller.image_store.get(image.identifier).metadata, result.json)

    def test_get_when_does_not_exist(self):
        controller = self.create_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist/metadata")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_put(self):
        self.display_controller.image_store.add(self.image)
        new_metadata = {"this": "that"}
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/{self.image.identifier}/metadata",
            data=BytesIO(str.encode(json.dumps(new_metadata))),
            content_type="application/json",
        )
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(new_metadata, self.display_controller.image_store.get(self.image.identifier).metadata)

    def test_put_when_image_not_exist(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/does-not-exist/metadata",
            data=BytesIO(str.encode(json.dumps({}))),
            content_type="application/json",
        )
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
