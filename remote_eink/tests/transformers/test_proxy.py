import unittest
from threading import Thread
from typing import Sequence

from remote_eink.multiprocess import ProxyReceiver
from remote_eink.tests._common import TestProxy
from remote_eink.tests.transformers._common import DummyImageTransformer
from remote_eink.tests.transformers.test_base import AbstractTest
from remote_eink.transformers import ImageTransformer
from remote_eink.transformers.base import SimpleImageTransformerSequence
from remote_eink.transformers.proxy import ProxyImageTransformer, ProxyImageTransformerSequence


class TestProxyImageTransformer(AbstractTest.TestImageTransformer[ProxyImageTransformer], TestProxy):
    """
    Test for `ProxyImageTransformer`.
    """
    def create_image_transformer(self) -> ProxyImageTransformer:
        receiver = self.setup_receiver(DummyImageTransformer())
        return ProxyImageTransformer(receiver.connector)


class TestProxyImageTransformerSequence(AbstractTest.TestImageTransformerSequence[ProxyImageTransformerSequence],
                                        TestProxy):
    """
    Tests `ProxyImageTransformerSequence`.
    """
    def create_image_transformer_sequence(self, image_transformers: Sequence[ImageTransformer]) \
            -> ProxyImageTransformerSequence:
        receiver = self.setup_receiver(SimpleImageTransformerSequence(image_transformers))
        return ProxyImageTransformerSequence(receiver.connector)


if __name__ == "__main__":
    unittest.main()
