import unittest
from io import BytesIO

from image_display_service.image import Image

_IDENTIFIER = "example-1"
_DATA = b"test"


class TestImage(unittest.TestCase):
    """
    Test for `Image`.
    """
    def test_get_data_with_cache(self):
        image = Image(_IDENTIFIER, lambda: BytesIO(_DATA).read(), cache_data=True)
        self.assertEqual(_IDENTIFIER, image.identifier)
        self.assertEqual(_DATA, image.data)
        self.assertEqual(_DATA, image.data)

    def test_get_data_without_cache(self):
        image = Image(_IDENTIFIER, lambda: _DATA, cache_data=False)
        self.assertEqual(_DATA, image.data)
        self.assertEqual(_DATA, image.data)

    def test_cache_toggle(self):
        for start_state in (True, False):
            with self.subTest(start_state=start_state):
                image = Image(_IDENTIFIER, lambda: _DATA, cache_data=start_state)
                self.assertEqual(_DATA, image.data)
                image.cache_data = not start_state
                self.assertEqual(_DATA, image.data)
                image.cache_data = start_state
                self.assertEqual(_DATA, image.data)


if __name__ == "__main__":
    unittest.main()
