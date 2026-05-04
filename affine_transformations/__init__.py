from .affine_transform import *
from krita import Krita

Krita.instance().addExtension(AffineTransform(Krita.instance()))