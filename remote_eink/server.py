import logging
import time
from threading import Thread, Semaphore
from typing import Optional

from remote_eink.app import destroy_app

_logger = logging.getLogger(__name__)

try:
    import requests
    from cheroot import wsgi
    from connexion import FlaskApp
except ImportError:
    _logger.error('"webserver" extra not installed')
    raise


_DEFAULT_START_TIMEOUT = 30.0
_DEFAULT_STOP_TIMEOUT = 60.0


class Server:
    """
    Model of the WSGI server.
    """

    @property
    def url(self) -> str:
        return f"http://{self.interface}:{self.port}"

    def __init__(
        self,
        app: FlaskApp,
        interface: str,
        port: int,
    ):
        """
        Constructor.
        :param app: copy of app ran on the server
        :param interface: interface server is bound to
        :param port: port the server is using
        """
        self.app: Optional[FlaskApp] = app
        self.interface = interface
        self.port = port
        self.server_set = Semaphore(0)
        self.server: Optional[wsgi.Server] = None
        self.thread: Optional[Thread] = None

    def stop(self, timeout_in_seconds: float = _DEFAULT_STOP_TIMEOUT):
        """
        Stops the server.
        :param timeout_in_seconds: number of seconds to wait for the server to gracefully stop
        """
        if self.server:
            self.server.stop()
            if self.app:
                destroy_app(self.app)
            if self.thread:
                self.thread.join(timeout_in_seconds)


def run(app: FlaskApp, *, interface: str = "0.0.0.0", port: int = 8080, server: Server = None):
    """
    Runs the given app in a production WSGI server.
    :param app: app to run on the server
    :param interface: interface to bind on
    :param port: port to use
    :param server: server model to update with information about the underlying WSGI server
    """
    wsgi_server = wsgi.Server((interface, port), app)

    if server:
        server.server = wsgi_server
        server.server_set.release()

    wsgi_server.start()


def start(app: FlaskApp, *, interface: str = "0.0.0.0", port: int = 8080) -> Server:
    """
    Starts the given app in a production WSGI server.
    :param app: app to run on the server
    :param interface: interface to bind on
    :param port: port to use
    :return: model of the running server
    """
    server = Server(app, interface, port)
    thread = Thread(target=run, kwargs=dict(app=app, server=server, interface=interface, port=port))
    thread.start()
    server.thread = thread

    acquired = server.server_set.acquire(timeout=_DEFAULT_START_TIMEOUT)
    if not acquired:
        _logger.error("Timeout waiting for server - stopping server")
        server.stop()
        raise
    assert server.server is not None
    _wait_until_responds(interface, port)

    return server


def _wait_until_responds(interface: str, port: int, timeout_in_seconds: float = _DEFAULT_START_TIMEOUT):
    """
    Waits for a HTTP server on the given interface and port to respond to HTTP requests.
    :param interface: interface server is bound to
    :param port: port the server is using
    :raises TimeoutError: timeout waiting for the server to start
    """
    url = f"http://{interface}:{port}"
    timeout = time.monotonic() + timeout_in_seconds
    i = 1
    while time.monotonic() < timeout:
        try:
            response = requests.head(url, timeout=0.1 * i)
            if 200 <= response.status_code <= 500:
                return True
        except requests.exceptions.ConnectionError:
            pass
        sleep_duration = min(0.1 * i, timeout - time.monotonic())
        time.sleep(sleep_duration)
        i += 1
    raise TimeoutError(f"Could not connect to: {url}")
