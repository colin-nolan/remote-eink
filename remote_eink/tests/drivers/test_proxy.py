import unittest

from remote_eink.drivers.proxy import ProxyDisplayDriver
from remote_eink.tests._common import TestProxy
from remote_eink.tests.drivers._common import DummyBaseDisplayDriver
from remote_eink.tests.drivers.test_base import AbstractTest, DisplayDriverType


class TestProxyDisplayDriver(AbstractTest.TestDisplayDriver[ProxyDisplayDriver], TestProxy):
    """
    Test for `ProxyDisplayDriver`.
    """
    def create_display_driver(self) -> DisplayDriverType:
        receiver = self.setup_receiver(DummyBaseDisplayDriver())
        return ProxyDisplayDriver(receiver.connector)


if __name__ == "__main__":
    unittest.main()
