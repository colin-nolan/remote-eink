from typing import Optional, List

from threading import Thread, Semaphore

import unittest

try:
    from get_port import find_free_port
    from remote_eink.server import start
    import requests

    WEBSERVER_INSTALLED = False
except ImportError:
    WEBSERVER_INSTALLED = True

from remote_eink.app import create_app, get_app_data
from remote_eink.tests._common import AppTestBase, create_dummy_display_controller, run_in_different_process

# Note: `get-port` is hard-coded to use this interface
_TEST_INTERFACE = "0.0.0.0"


@unittest.skipIf(WEBSERVER_INSTALLED, "Optional `webserver` not installed")
class TestRun(AppTestBase):
    """
    Test for `run`.
    """

    def setUp(self):
        self.port, _ = find_free_port()

    def test_start(self):
        controllers = [create_dummy_display_controller()]
        app = create_app(controllers)
        server = start(app, interface=_TEST_INTERFACE, port=self.port)
        try:
            response = requests.get(f"{server.url}/display", timeout=30)
            self.assertEqual(200, response.status_code)
            self.assertEqual([{"id": controller.identifier} for controller in controllers], response.json())
        finally:
            server.stop()

    def test_stop_server(self):
        for i in range(3):
            app = create_app([])
            # Asserting must have stopped on second+ run as using same port
            server = start(app, interface=_TEST_INTERFACE, port=self.port)
            try:
                response = requests.get(f"{server.url}/display", timeout=30)
                self.assertEqual(200, response.status_code)
            finally:
                server.stop()

    def test_change_display_controllers_after_server_started(self):
        app = create_app([])
        server = start(app, interface=_TEST_INTERFACE, port=self.port)
        try:
            response = run_in_different_process(requests.get, f"{server.url}/display", timeout=30)
            self.assertEqual(200, response.status_code)
            self.assertEqual([], response.json())

            display_controller = create_dummy_display_controller()
            get_app_data(app).add_display_controller(display_controller)
            response = run_in_different_process(requests.get, f"{server.url}/display", timeout=30)
            self.assertEqual([{"id": display_controller.identifier}], response.json())
        finally:
            server.stop()

    def test_simultaneous_requests(self):
        display_controller = create_dummy_display_controller()
        app = create_app([display_controller])
        server = start(app, interface=_TEST_INTERFACE, port=self.port)
        exceptions: List[Optional[Exception]] = []
        completed_semaphore = Semaphore(0)

        def do_request():
            try:
                response = run_in_different_process(requests.get, f"{server.url}/display", timeout=15)
                self.assertEqual([{"id": display_controller.identifier}], response.json())
            except Exception as e:
                exceptions.append(e)
            finally:
                completed_semaphore.release()

        number_of_requests = 10
        try:
            for i in range(number_of_requests):
                Thread(target=do_request).start()
            for i in range(number_of_requests):
                completed_semaphore.acquire()
            for exception in exceptions:
                raise exception
            pass
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
