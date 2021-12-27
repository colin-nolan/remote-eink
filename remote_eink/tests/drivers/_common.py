from remote_eink.drivers.base import BaseDisplayDriver


class DummyBaseDisplayDriver(BaseDisplayDriver):
    """
    Dummy display driver.
    """

    def _display(self, image_data: bytes):
        pass

    def _clear(self):
        pass

    def _sleep(self):
        pass

    def _wake(self):
        pass
