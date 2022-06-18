import json
from http import HTTPStatus
from io import BytesIO

from requests_toolbelt import MultipartDecoder
from requests_toolbelt.multipart import decoder
from requests_toolbelt.multipart.decoder import BodyPart

from remote_eink.api.display._common import ImageTypeToMimeTypes
from remote_eink.images import FunctionBasedImage, ImageType
from remote_eink.tests._common import create_image, set_content_type_header
from remote_eink.tests.api.display.image._common import BaseTestDisplayImage, create_image_upload_content
from remote_eink.transformers.rotate import ROTATION_METADATA_KEY


class TestDisplayImage(BaseTestDisplayImage):
    """
    Tests for the `/display/{displayId}/image` endpoint.
    """

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

    def test_get(self):
        metadata = {ROTATION_METADATA_KEY: 42}
        image = create_image(metadata=metadata)
        self.display_controller.image_store.add(image)
        result = self.client.get(f"/display/{self.display_controller.identifier}/image/{image.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)

        multipart_data = MultipartDecoder(result.data, result.content_type)
        metadata_part = tuple(
            filter(lambda part: b'name="metadata"' in part.headers[b"Content-Disposition"], multipart_data.parts)
        )[0]
        data_part = tuple(
            filter(lambda part: b'name="data"' in part.headers[b"Content-Disposition"], multipart_data.parts)
        )[0]

        self.assertEqual(metadata, json.loads(metadata_part.text))
        self.assertEqual(image.data, data_part.content)

    def test_get_when_does_not_exist(self):
        result = self.client.get(f"/display/{self.display_controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_post(self):
        assert self.image not in self.display_controller.image_store
        result = self.client.post(
            f"/display/{self.display_controller.identifier}/image",
            data=create_image_upload_content(self.image),
        )
        self.assertEqual(HTTPStatus.CREATED, result.status_code, result)
        image_identifier = result.json
        expected_image = FunctionBasedImage(
            image_identifier, lambda: self.image.data, self.image.type, self.image.metadata
        )
        self.assertEqual(expected_image, self.display_controller.image_store.get(image_identifier))

    def test_post_with_unspecific_image_content_type(self):
        result = self.client.post(
            f"/display/{self.display_controller.identifier}/image",
            data={
                "metadata": (BytesIO(str.encode(json.dumps(self.image.metadata))), None, "application/json"),
                "data": (BytesIO(self.image.data), "blob", "application/octet-stream"),
            },
        )
        self.assertEqual(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, result.status_code, result)

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
            data=create_image_upload_content(self.image),
            content_type="multipart/form-data",
        )
        self.assertEqual(HTTPStatus.CREATED, result.status_code)
        self.assertEqual(self.image, self.display_controller.image_store.get(self.image.identifier))

    def test_put_with_duplicate_id(self):
        image_1 = create_image()
        self.client.put(
            f"/display/{self.display_controller.identifier}/image/{image_1.identifier}",
            data=create_image_upload_content(image_1),
            content_type="multipart/form-data",
        )
        image_2 = create_image()
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/{image_1.identifier}",
            data=create_image_upload_content(image_2),
            content_type="multipart/form-data",
        )
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(image_2.data, self.display_controller.image_store.get(image_1.identifier).data)

    def test_put_invalid_image(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image/{self.image.identifier}",
            data={
                "metadata": (BytesIO(str.encode(json.dumps({}))), None, "application/json"),
                "data": (BytesIO(b"invalid"), "blob", ImageTypeToMimeTypes[ImageType.PNG][0]),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, result.status_code)

    def test_put_display_not_exist(self):
        result = self.client.put(
            f"/display/does-not-exist/image/{self.image.identifier}", data=create_image_upload_content(self.image)
        )
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
