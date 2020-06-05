from pathlib import Path

from remote_eink.images import Image, ImageType
from remote_eink.tests._resources import BLACK_IMAGE_LOCATION, WHITE_IMAGE_LOCATION

WHITE_IMAGE = Image("white-image", lambda: Path(WHITE_IMAGE_LOCATION).read_bytes(), ImageType.JPG)
BLACK_IMAGE: Image = Image("black-image", lambda: Path(BLACK_IMAGE_LOCATION).read_bytes(), ImageType.PNG)
