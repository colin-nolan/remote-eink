import json

from flask_testing import TestCase
import unittest

from image_display_service.display.controllers import DisplayController
from image_display_service.display.drivers import DummyDisplayDriver
from image_display_service.web_api import create_app

EXAMPLE_CONTROLLERS = (DisplayController(DummyDisplayDriver()), DisplayController(DummyDisplayDriver()))


class DisplayApiTests(TestCase):
    """
    Tests for the `/display` endpoint.
    """
    def create_app(self):
        # TODO: args
        app = create_app(EXAMPLE_CONTROLLERS).app
        app.config["TESTING"] = True
        return app

    def test_search_displays(self):
        result = self.client.get("/display")
        self.assertEqual(200, result.status_code)
        self.assertCountEqual([controller.identifier for controller in EXAMPLE_CONTROLLERS], json.loads(result.json))


if __name__ == '__main__':
    unittest.main()
