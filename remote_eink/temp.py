from get_port import find_free_port

from remote_eink.app import create_app
from remote_eink.server import start, run
from remote_eink.tests._common import create_dummy_display_controller

port, _ = find_free_port()
controller = create_dummy_display_controller()
print(f"http://localhost:{port}/display/{controller.identifier}/image")
server = run(create_app((controller,)), interface="localhost", port=port)
