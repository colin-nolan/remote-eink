import unittest

try:
    from get_port import find_free_port
    from remote_eink.server import start
    import requests
    WEBSERVER_INSTALLED = False
except ImportError:
    WEBSERVER_INSTALLED = True

from remote_eink.app import create_app
from remote_eink.tests._common import TestBase, create_dummy_display_controller

# Note: `get-port` is hard-coded to use this interface
_TEST_INTERFACE = "0.0.0.0"


@unittest.skipIf(WEBSERVER_INSTALLED, "Optional `webserver` not installed")
class TestRun(TestBase):
    """
    Test for `run`.
    """
    def test_start(self):
        controllers = [create_dummy_display_controller()]
        app = create_app(controllers)
        port, _ = find_free_port()
        server = start(app, interface=_TEST_INTERFACE, port=port)
        try:
            response = requests.get(f"{server.url}/display", timeout=30)
            self.assertEqual(200, response.status_code)
            self.assertEqual([{"id": controller.identifier} for controller in controllers], response.json())
        finally:
            server.stop()

    def test_stop_server(self):
        app = create_app([])
        port, _ = find_free_port()
        for i in range(3):
            # Asserting must have stopped on second+ run as using same port
            server = start(app, interface=_TEST_INTERFACE, port=port)
            try:
                response = requests.get(f"{server.url}/display", timeout=30)
                self.assertEqual(200, response.status_code)
            finally:
                server.stop()


if __name__ == "__main__":
    unittest.main()
