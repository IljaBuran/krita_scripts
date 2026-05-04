from .canny_edges import *
from krita import Krita

# Register extension
Krita.instance().addExtension(CannyEdgesExtension(Krita.instance()))