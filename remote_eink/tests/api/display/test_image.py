import json
from http import HTTPStatus

import requests
from get_port import find_free_port
from io import BytesIO, StringIO

from flask import url_for
from requests_toolbelt import MultipartEncoder

from remote_eink.api.display._common import ImageTypeToMimeType
from remote_eink.app import create_app
from remote_eink.images import ImageType, FunctionBasedImage, Image
from remote_eink.server import start
from remote_eink.tests._common import create_image, AppTestBase, set_content_type_header


class TestDisplayImage(AppTestBase):
    """
    Tests for the `/display/{displayId}/image` endpoint.
    """

    def setUp(self):
        super().setUp()
        self.image = create_image(rotation=90)

    def test_list(self):
        for number_of_images in range(5):
            with self.subTest(number_of_images=number_of_images):
                controller = self.create_display_controller(number_of_images=number_of_images)
                result = self.client.get(f"/display/{controller.identifier}/image")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertCountEqual(
                    ({"id": image.identifier} for image in controller.image_store.list()), result.json
                )

    def test_list_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_image(self):
        for image_type in ImageType:
            with self.subTest(image_type=image_type.name):
                display_controller = self.create_display_controller()
                image = create_image(image_type=image_type)
                display_controller.image_store.add(image)
                result = self.client.get(f"/display/{display_controller.identifier}/image/{image.identifier}")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertEqual(ImageTypeToMimeType[image_type], result.mimetype)
                self.assertEqual(display_controller.image_store.get(image.identifier).data, result.data)

    def test_get_when_does_not_exist(self):
        controller = self.create_display_controller()
        result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_post(self):
        assert self.image not in self.display_controller.image_store
        result = self.client.post(
            f"/display/{self.display_controller.identifier}/image",
            data=_create_image_upload_content(self.image),
        )
        self.assertEqual(HTTPStatus.CREATED, result.status_code, result)
        image_identifier = result.json
        expected_image = FunctionBasedImage(image_identifier, lambda: self.image.data, self.image.type)
        self.assertEqual(expected_image, self.display_controller.image_store.get(image_identifier))

    def test_post_to_specific_id(self):
        result = self.client.post(
            f"/display/{self.display_controller.identifier}/image/{self.image.identifier}",
            data=self.image.data,
            headers=set_content_type_header(self.image),
        )
        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, result.status_code)

    def test_put(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/{self.image.identifier}",
            data=_create_image_upload_content(self.image),
            content_type="multipart/form-data",
        )
        self.assertEqual(HTTPStatus.CREATED, result.status_code)
        self.assertEqual(self.image, self.display_controller.image_store.get(self.image.identifier))

    def test_put_with_duplicate_id(self):
        image_1 = create_image()
        self.client.put(
            f"/display/{self.display_controller.identifier}/image/{image_1.identifier}",
            data=_create_image_upload_content(image_1),
            content_type="multipart/form-data",
        )
        image_2 = create_image()
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/{image_1.identifier}",
            data=_create_image_upload_content(image_2),
            content_type="multipart/form-data",
        )
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(image_2.data, self.display_controller.image_store.get(image_1.identifier).data)

    def test_put_display_not_exist(self):
        result = self.client.put(f"/display/does-not-exist/image/{self.image.identifier}", data=_create_image_upload_content(self.image))
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image(self):
        self.display_controller.image_store.add(self.image)
        result = self.client.delete(f"/display/{self.display_controller.identifier}/image/{self.image.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertNotIn(self.image, self.display_controller.image_store)

    def test_delete_image_does_not_exist(self):
        result = self.client.delete(f"/display/{self.display_controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image_display_does_not_exist(self):
        result = self.client.delete(f"/display/does-not-exist/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)


def _create_image_upload_content(image: Image):
    return {
        "metadata": (BytesIO(str.encode(json.dumps({"rotation": image.rotation}))), None, "application/json"),
        "data": (BytesIO(image.data), "blob", ImageTypeToMimeType[image.type]),
    }
