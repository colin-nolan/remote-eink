import os

from remote_eink.app import create_app
from remote_eink.controllers import AutoCyclingDisplayController
from remote_eink.drivers.local import LocalDisplayDriver
from remote_eink.images import DataBasedImage, ImageType
from remote_eink.server import start, run
from remote_eink.storage.images import InMemoryImageStore

IMAGE_DIRECTORY = f"{os.path.dirname(__file__)}/../tests/_resources"


def main():
    driver = LocalDisplayDriver()
    driver.start()

    image_store = InMemoryImageStore()

    display_controller = AutoCyclingDisplayController(
        driver, image_store, "example-display", cycle_image_after_seconds=1
    )
    display_controller.image_store.add(
        DataBasedImage(
            "black",
            open(f"{IMAGE_DIRECTORY}/black.png", "rb").read(),
            ImageType.PNG,
        )
    )
    display_controller.image_store.add(
        DataBasedImage(
            "white",
            open(f"{IMAGE_DIRECTORY}/white.jpg", "rb").read(),
            ImageType.JPG,
        )
    )
    display_controller.start()

    app = create_app((display_controller,))
    run(app, interface="localhost", port=8080)                # Blocking
    # server = start(app, interface="localhost", port=8080)   # Non-blocking alternative

    # If we wanted to tear everything down (assuming non-blocking app)
    # server.stop()
    # display_controller.stop()
    # driver.stop()


if __name__ == "__main__":
    main()
