from http import HTTPStatus

from remote_eink.tests._common import AppTestBase
from remote_eink.tests._common import DummyImageTransformer


class TestImageTransformer(AppTestBase):
    """
    Tests for the `/display/{displayId}/image-transformer` endpoint.
    """
    def setUp(self):
        image_transformers = []
        for i in range(3):
            image_transformer = DummyImageTransformer(configuration={"test": i}, description=f"example-{i}")
            image_transformers.append(image_transformer)
        self.controller = self.create_dummy_display_controller(image_transformers=image_transformers)

    def test_list(self):
        result = self.client.get(f"/display/{self.controller.identifier}/image-transformer")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertCountEqual(({"id": transformer.identifier} for transformer in self.controller.image_transformers),
                              result.json)

    def test_list_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get(self):
        for position, transformer in enumerate(self.controller.image_transformers):
            result = self.client.get(
                f"/display/{self.controller.identifier}/image-transformer/{transformer.identifier}")
            self.assertEqual(HTTPStatus.OK, result.status_code)
            self.assertEqual(transformer.identifier, result.json["id"])
            self.assertEqual(transformer.description, result.json["description"])
            self.assertEqual(transformer.active, result.json["active"])
            self.assertEqual(position, result.json["position"])
            self.assertEqual(transformer.configuration, result.json["configuration"])


    # def test_get_image(self):
    #     for image_type in ImageType:
    #         with self.subTest(image_type=image_type.name):
    #             controller = self.create_dummy_display_controller()
    #             image = create_image(image_type)
    #             controller.image_store.add(image)
    #             result = self.client.get(f"/display/{controller.identifier}/image/{image.identifier}")
    #             self.assertEqual(HTTPStatus.OK, result.status_code)
    #             self.assertEqual(ImageTypeToMimeType[image_type], result.mimetype)
    #             self.assertEqual(controller.image_store.get(image.identifier).data, result.data)
    #
    # def test_get_when_does_not_exist(self):
    #     controller = self.create_dummy_display_controller()
    #     result = self.client.get(f"/display/{controller.identifier}/image/does-not-exist")
    #     self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
    #
    # def test_save(self):
    #     controller = self.create_dummy_display_controller()
    #     image = create_image()
    #     result = self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data,
    #                               headers=set_content_type_header(image))
    #     self.assertEqual(HTTPStatus.CREATED, result.status_code)
    #
    # def test_save_with_duplicate_id(self):
    #     controller = self.create_dummy_display_controller()
    #     image_1 = create_image()
    #     self.client.post(f"/display/{controller.identifier}/image/{image_1.identifier}", data=image_1.data,
    #                      headers=set_content_type_header(image_1))
    #     image_2 = create_image()
    #     result = self.client.post(f"/display/{controller.identifier}/image/{image_1.identifier}", data=image_2.data,
    #                               headers=set_content_type_header(image_2))
    #     self.assertEqual(HTTPStatus.CONFLICT, result.status_code)
    #
    # def test_save_no_content_type_header(self):
    #     controller = self.create_dummy_display_controller()
    #     image = create_image()
    #     result = self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data)
    #     self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)
    #
    # def test_save_display_not_exist(self):
    #     image = create_image()
    #     result = self.client.post(f"/display/does-not-exist/image/{image.identifier}", data=image.data)
    #     self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
    #
    # def test_delete_image(self):
    #     controller = self.create_dummy_display_controller()
    #     image = create_image()
    #     self.client.post(f"/display/{controller.identifier}/image/{image.identifier}", data=image.data,
    #                      headers=set_content_type_header(image))
    #     result = self.client.delete(f"/display/{controller.identifier}/image/{image.identifier}")
    #     self.assertEqual(HTTPStatus.OK, result.status_code)
    #
    # def test_delete_image_does_not_exist(self):
    #     controller = self.create_dummy_display_controller()
    #     result = self.client.delete(f"/display/{controller.identifier}/image/does-not-exist")
    #     self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
    #
    # def test_delete_image_display_does_not_exist(self):
    #     result = self.client.delete(f"/display/does-not-exist/image/does-not-exist")
    #     self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)
