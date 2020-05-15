from remote_eink.models import Image, ImageType

EXAMPLE_IMAGE_1 = Image("example-1", lambda: b"abc", ImageType.PNG)
EXAMPLE_IMAGE_2 = Image("example-2", lambda: b"def", ImageType.JPG)
