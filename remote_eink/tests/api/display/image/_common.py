import json
from io import BytesIO

from remote_eink.api.display._common import ImageTypeToMimeType
from remote_eink.images import Image
from remote_eink.tests._common import create_image, AppTestBase


class BaseTestDisplayImage(AppTestBase):
    def setUp(self):
        super().setUp()
        self.image = create_image(rotation=90)


def create_image_upload_content(image: Image):
    return {
        "metadata": (BytesIO(str.encode(json.dumps({"rotation": image.rotation}))), None, "application/json"),
        "data": (BytesIO(image.data), "blob", ImageTypeToMimeType[image.type]),
    }
