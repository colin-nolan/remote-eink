from remote_eink.tests.transformers.test_base import AbstractTest
from remote_eink.transformers.simple import SimpleImageTransformer


class TestSimpleImageTransformer(
    AbstractTest.TestImageTransformer[SimpleImageTransformer],
):
    def create_image_transformer(self, *args, **kwargs) -> SimpleImageTransformer:
        return SimpleImageTransformer()
