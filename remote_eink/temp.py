from remote_eink.app import create_app
from remote_eink.controllers import BaseDisplayController
from remote_eink.drivers.local import LocalDisplayDriver
from remote_eink.server import run
from remote_eink.storage.images import InMemoryImageStore

driver = LocalDisplayDriver()
image_store = InMemoryImageStore()
display_controller = BaseDisplayController(driver, image_store, "example-store")
app = create_app((display_controller,))
run(app)
