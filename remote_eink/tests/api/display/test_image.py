from http import HTTPStatus

from remote_eink.api.display._common import ImageTypeToMimeType
from remote_eink.images import ImageType, FunctionBasedImage
from remote_eink.tests._common import create_image, AppTestBase, set_content_type_header


class TestDisplayImage(AppTestBase):
    """
    Tests for the `/display/{displayId}/image` endpoint.
    """
    def test_list(self):
        for number_of_images in range(5):
            with self.subTest(number_of_images=number_of_images):
                controller = self.create_display_controller(number_of_images=number_of_images)
                result = self.client.get(f"/display/{controller.identifier}/image")
                self.assertEqual(HTTPStatus.OK, result.status_code)
                self.assertCountEqual(({"id": image.identifier} for image in controller.image_store.list()),
                                      result.json)

    def test_list_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_image(self):
        for image_type in ImageType:
            with self.subTest(image_type=image_type.name):
                display_controller = self.create_display_controller()
                image = create_image(image_type)
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
        image = create_image()
        assert image not in self.display_controller.image_store
        result = self.client.post(f"/display/{self.display_controller.identifier}/image",
                                  data=image.data, headers=set_content_type_header(image))
        self.assertEqual(HTTPStatus.CREATED, result.status_code, result)
        image_identifier = result.json
        expected_image = FunctionBasedImage(image_identifier, lambda: image.data, image.type)
        self.assertEqual(expected_image, self.display_controller.image_store.get(image_identifier))

    def test_post_to_specific_id(self):
        image = create_image()
        result = self.client.post(f"/display/{self.display_controller.identifier}/image/{image.identifier}",
                                  data=image.data, headers=set_content_type_header(image))
        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, result.status_code)

    def test_put(self):
        image = create_image()
        assert image not in self.display_controller.image_store
        result = self.client.put(f"/display/{self.display_controller.identifier}/image/{image.identifier}",
                                 data=image.data, headers=set_content_type_header(image))
        self.assertEqual(HTTPStatus.CREATED, result.status_code)
        self.assertEqual(image, self.display_controller.image_store.get(image.identifier))

    def test_put_with_duplicate_id(self):
        image_1 = create_image()
        self.client.put(f"/display/{self.display_controller.identifier}/image/{image_1.identifier}", data=image_1.data,
                        headers=set_content_type_header(image_1))
        image_2 = create_image()
        result = self.client.put(f"/display/{self.display_controller.identifier}/image/{image_1.identifier}",
                                 data=image_2.data, headers=set_content_type_header(image_2))
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(image_2.data, self.display_controller.image_store.get(image_1.identifier).data)

    def test_put_no_content_type_header(self):
        controller = self.create_display_controller()
        image = create_image()
        result = self.client.put(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data)
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_put_display_not_exist(self):
        image = create_image()
        result = self.client.put(f"/display/does-not-exist/image/{image.identifier}", data=image.data)
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image(self):
        image = create_image()
        self.display_controller.image_store.add(image)
        result = self.client.delete(f"/display/{self.display_controller.identifier}/image/{image.identifier}")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertNotIn(image, self.display_controller.image_store)

    def test_delete_image_does_not_exist(self):
        controller = self.create_display_controller()
        result = self.client.delete(f"/display/{controller.identifier}/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_delete_image_display_does_not_exist(self):
        result = self.client.delete(f"/display/does-not-exist/image/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
