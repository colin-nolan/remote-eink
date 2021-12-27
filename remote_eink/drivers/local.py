import io
import logging
import tkinter as tk
from multiprocessing import Process
from multiprocessing.connection import Pipe, Connection
from threading import Thread

import math

from remote_eink.drivers.base import BaseDisplayDriver

logger = logging.getLogger(__name__)

try:
    from PIL import ImageTk, Image
except ImportError:
    # TODO
    logger.error('"TODO" extra not installed')
    raise


class LocalDisplayDriver(BaseDisplayDriver):
    """
    Local display device driver.
    """

    def __init__(self):
        super().__init__()
        self._parent_connection, self._child_connection = Pipe()

    def _display(self, image_data: bytes):
        self._parent_connection.send(image_data)

    def _clear(self):
        self._parent_connection.send(b"")

    def _sleep(self):
        pass

    def _wake(self):
        pass

    def start(self):
        # Mac (at least) requires UI updates to be made on the main thread. Running the display window as a separate
        # process to separate its need to be on the main.
        Process(target=_run_local_screen_window, args=(self._child_connection,)).start()


def _run_local_screen_window(connection: Connection):
    screen_window = _LocalScreenWindow(connection)
    screen_window.run()


class _LocalScreenWindow:
    """
    Screen window that displays image data communicated on multiprocessing pipe.
    """

    DEFAULT_PIXEL_WIDTH = 500
    DEFAULT_PIXEL_HEIGHT = 500

    @staticmethod
    def _create_window(pixel_width: int, pixel_height: int):
        window = tk.Tk()
        window.title("Local Display Device")
        window.geometry(f"{pixel_width}x{pixel_height}")
        return window

    def __init__(
        self,
        communication_pipe: Connection,
        pixel_width: int = DEFAULT_PIXEL_WIDTH,
        pixel_height: int = DEFAULT_PIXEL_HEIGHT,
    ):
        super().__init__()
        self._communication_pipe = communication_pipe
        self._window = _LocalScreenWindow._create_window(pixel_width, pixel_height)

    def run(self):
        Thread(target=self._handle_display_requests).start()
        self._window.mainloop()

    def _handle_display_requests(self):
        while True:
            received = self._communication_pipe.recv()
            self._display(received)

    def _display(self, image_data: bytes):
        for widget in self._window.winfo_children():
            widget.destroy()

        if len(image_data) > 0:
            pillow_image = Image.open(io.BytesIO(image_data))
            # Scale large images down (uniformly) to fit the window
            scaler = min(
                (self._window.winfo_width() / pillow_image.width, self._window.winfo_height() / pillow_image.height, 1)
            )
            pillow_image = pillow_image.resize(
                (math.floor(pillow_image.width * scaler), math.floor(pillow_image.height * scaler))
            )

            tk_image = ImageTk.PhotoImage(pillow_image)
            label = tk.Label(self._window, image=tk_image)
            label.photo = tk_image
            label.pack(side="bottom", fill="both", expand=True)
