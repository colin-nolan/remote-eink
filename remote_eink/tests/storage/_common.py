from pathlib import Path

from remote_eink.images import ImageType, FunctionBasedImage, DataBasedImage
from remote_eink.tests._resources import BLACK_IMAGE_LOCATION, WHITE_IMAGE_LOCATION

WHITE_IMAGE = DataBasedImage("white-image", Path(WHITE_IMAGE_LOCATION).read_bytes(), ImageType.JPG)
BLACK_IMAGE = FunctionBasedImage("black-image", lambda: Path(BLACK_IMAGE_LOCATION).read_bytes(), ImageType.PNG)
