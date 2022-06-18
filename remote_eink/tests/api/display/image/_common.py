import json
from io import BytesIO
from typing import Dict, Tuple, Optional

from remote_eink.api.display._common import ImageTypeToMimeTypes
from remote_eink.images import Image
from remote_eink.tests._common import create_image, AppTestBase
from remote_eink.transformers.rotate import ROTATION_METADATA_KEY


class BaseTestDisplayImage(AppTestBase):
    def setUp(self):
        super().setUp()
        self.image = create_image(metadata={ROTATION_METADATA_KEY: 90})


def create_image_upload_content(image: Image) -> Dict[str, Tuple[BytesIO, Optional[str], str]]:
    return {
        "metadata": (BytesIO(str.encode(json.dumps(image.metadata))), None, "application/json"),
        "data": (BytesIO(image.data), "blob", ImageTypeToMimeTypes[image.type][0]),
    }
