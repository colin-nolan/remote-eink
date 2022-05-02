from remote_eink.transformers.base import ImageTransformer, ImageTypeToPillowFormat
from remote_eink.transformers.sequence import SimpleImageTransformerSequence, ImageTransformerSequence
from remote_eink.transformers.rotate import (
    RotateConfigurationParameter,
    RotateImageTransformer,
    ImageRotationAwareRotateImageTransformer, ROTATION_IMAGE_TRANSFORMER_AVAILABLE,
)

_transformers = []
if ROTATION_IMAGE_TRANSFORMER_AVAILABLE:
    _transformers.append(ImageRotationAwareRotateImageTransformer())
DEFAULT_TRANSFORMERS = tuple(_transformers)
