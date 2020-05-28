from http import HTTPStatus

from remote_eink.app import get_synchronised_app_storage
from remote_eink.tests._common import AppTestBase, DummyImageTransformer
from remote_eink.transformers.rotate import RotateImageTransformer, RotateConfigurationParameter


class TestImageTransformer(AppTestBase):
    """
    Tests for the `/display/{displayId}/image-transformer` endpoint.
    """
    def setUp(self):
        self.image_transformers = []
        for i in range(3):
            image_transformer = DummyImageTransformer(configuration={"test": i}, description=f"example-{i}")
            self.image_transformers.append(image_transformer)
        self.create_display_controller(image_transformers=self.image_transformers)

    def test_list(self):
        result = self.client.get(f"/display/{self.display_controller.identifier}/image-transformer")
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertCountEqual(({"id": transformer.identifier} for transformer in self.display_controller.image_transformers),
                              result.json)

    def test_list_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get(self):
        for position, image_transformer in enumerate(self.display_controller.image_transformers):
            result = self.client.get(
                f"/display/{self.display_controller.identifier}/image-transformer/{image_transformer.identifier}")
            self.assertEqual(HTTPStatus.OK, result.status_code)
            self.assertEqual(image_transformer.identifier, result.json["id"])
            self.assertEqual(image_transformer.description, result.json["description"])
            self.assertEqual(image_transformer.active, result.json["active"])
            self.assertEqual(position, result.json["position"])
            self.assertEqual(image_transformer.configuration, result.json["configuration"])

    def test_get_when_display_does_not_exist(self):
        result = self.client.get(f"/display/does-not-exist/image-transformer/1")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_get_when_image_transformer_does_not_exist(self):
        result = self.client.get(f"/display/{self.display_controller.identifier}/image-transformer/does-not-exist")
        self.assertEqual(HTTPStatus.NOT_FOUND, result.status_code)

    def test_put(self):
        with get_synchronised_app_storage().update_display_controller(self.display_controller.identifier) \
                as display_controller:
            image_transformer = RotateImageTransformer(angle=0.0, expand=False, fill_color="green")
            display_controller.image_transformers.add(image_transformer)
            assert image_transformer in display_controller.image_transformers

        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{image_transformer.identifier}",
            json={"configuration": {
                RotateConfigurationParameter.ANGLE.value: 90.0,
                RotateConfigurationParameter.EXPAND.value: True,
                RotateConfigurationParameter.FILL_COLOR.value: "silver"
            }})

        self.assertEqual(HTTPStatus.OK, result.status_code)
        display_controller = get_synchronised_app_storage().get_display_controller(display_controller.identifier)
        image_transformer = display_controller.image_transformers.get_by_id(image_transformer.identifier)[0]
        self.assertEqual(90.0, image_transformer.angle)
        self.assertEqual(True, image_transformer.expand)
        self.assertEqual("silver", image_transformer.fill_color)

    def test_put_with_invalid_parameter(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{self.image_transformers[0].identifier}",
            json={"invalid-config-property": True})
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_put_with_invalid_configuration_parameters(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{self.image_transformers[0].identifier}",
            json={"configuration": {"invalid-config-property": True}})
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_put_with_mix_valid_invalid_configuration_parameters(self):
        image_transformer = self.image_transformers[0]
        image_transformer.dummy_configuration = {}
        assert image_transformer.configuration == {}
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{image_transformer.identifier}",
            json={"configuration": {"invalid-config-property": True, "valid": False}})
        self.assertEqual({}, image_transformer.configuration)
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)

    def test_put_position_change(self):
        first = self.display_controller.image_transformers[0]
        assert self.display_controller.image_transformers.get_position(first) == 0
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{first.identifier}", json={"position": 2})
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.synchronise_display_controllers()
        self.assertEqual(2, self.display_controller.image_transformers.get_position(first))

    def test_put_position_no_change(self):
        first = self.display_controller.image_transformers[0]
        assert self.display_controller.image_transformers.get_position(first) == 0
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{first.identifier}", json={"position": 0})
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual(0, self.display_controller.image_transformers.get_position(first))

    def test_put_position_beyond_end(self):
        image_transformer_id = self.display_controller.image_transformers[1].identifier
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/{image_transformer_id}",
            json={"position": len(self.display_controller.image_transformers) + 10})
        self.assertEqual(HTTPStatus.OK, result.status_code)
        display_controller = get_synchronised_app_storage().get_display_controller(self.display_controller.identifier)
        self.assertEqual(len(display_controller.image_transformers) - 1,
                         display_controller.image_transformers.get_position(image_transformer_id))

    def test_put_position_before_start(self):
        result = self.client.put(
            f"/display/{self.display_controller.identifier}/image-transformer/"
            f"{self.display_controller.image_transformers[1].identifier}",
            json={"position": -1})
        self.assertEqual(HTTPStatus.BAD_REQUEST, result.status_code)
