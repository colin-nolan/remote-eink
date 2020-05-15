from remote_eink.tests.api._common import create_dummy_display_controller
from remote_eink.web_api import create_app

app = create_app([create_dummy_display_controller()])
app.run()
