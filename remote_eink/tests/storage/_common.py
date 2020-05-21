from pathlib import Path

from remote_eink.models import Image, ImageType
from remote_eink.tests._resources import BLACK_IMAGE_LOCATION, WHITE_IMAGE_LOCATION

WHITE_IMAGE = Image("example-1", lambda: Path(WHITE_IMAGE_LOCATION).read_bytes(), ImageType.JPG)
BLACK_IMAGE = Image("example-2", lambda: Path(BLACK_IMAGE_LOCATION).read_bytes(), ImageType.PNG)
