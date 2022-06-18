from http import HTTPStatus

from remote_eink.api.display._common import ImageTypeToMimeTypes
from remote_eink.images import ImageType
from remote_eink.tests._common import create_image
from remote_eink.tests.api.display.image._common import BaseTestDisplayImage


class TestDisplayImageData(BaseTestDisplayImage):
    """
    Tests for the `/display/{displayId}/image/data` endpoint.
    """

    def test_get(self):
        for image_type in ImageType:
            with self.subTest(image_type=image_type.name):
                display_controller = self.create_display_controller()
                image = create_image(image_type=image_type)
                display_controller.image_store.add(image)
                result = self.client.get(f"/display/{display_controller.identifier}/image/{image.identifier}/data")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertIn(result.mimetype, ImageTypeToMimeTypes[image_type])
                self.assertEqual(display_controller.image_store.get(image.identifier).data, result.data)

    def test_get_when_does_not_exist(self):
        controller = self.create_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist/data")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
